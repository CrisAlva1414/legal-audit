#!/usr/bin/env python3
"""scan.py — CLI agregador de los 6 detectores.

Uso:
    python3 scan.py <repo-auditar> [--json salida.json]

- Carga el pack de obligaciones propio de la skill (obligations.json).
- Corre los 6 detectores (scripts/detectors/*.py) contra el repo auditado.
- Agrega hallazgos con su `techo_de_veredicto` (heredado del pack: un
  detector jamás puede subir el techo — doctrine.md:118-145).
- Emite el JSON con: resumen por detector/prioridad_revision/jurisdicción, lista de
  hallazgos, y la cobertura de obligaciones (incluido el hueco honesto:
  qué obligaciones del pack NINGÚN detector chequea).
- NUNCA emite un veredicto global. Solo hechos `archivo:línea`.

Read-only sobre <repo-auditar>. Solo stdlib. Sin red.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

# <raiz>/skills/legal-audit/scripts/scan.py
SKILL_ROOT = Path(__file__).resolve().parents[1]
DETECTORS_DIR = Path(__file__).resolve().parent / "detectors"
OBLIGACIONES_JSON = SKILL_ROOT / "references" / "obligations" / "obligations.json"

# common.py es el mismo módulo que importan los detectores (sys.modules):
# las banderas (INCLUDE_SECRETS) y los estadísticos (STATS) se comparten.
sys.path.insert(0, str(DETECTORS_DIR))
import common  # noqa: E402

DETECTORS = [
    "pii_sinks",
    "consent_flow",
    "dsar_endpoints",
    "pii_in_logs",
    "security_config",
    "minors_and_voice",
]

PRIORIDAD_ORDEN = ["ALTA", "MEDIA", "BAJA", "INFO"]

# Defensa en profundidad (ALTA-2): si un detector excede este tiempo se
# registra `timeout: <detector>` y el scan sigue con los demás.
DETECTOR_TIMEOUT_SEG = 60

_HAS_ALARM = hasattr(signal, "SIGALRM")


class _DetectorTimeout(RuntimeError):
    """Un detector excedió el tope de tiempo; no aborta el resto del scan."""


def _scan_con_timeout(mod, target):
    """Corre `mod.scan(target)` con `signal.alarm` (Unix)."""
    if not _HAS_ALARM:
        return mod.scan(target)

    def _alarm(_signum, _frame):
        raise _DetectorTimeout(f"timeout: {mod.__name__}")

    prev = signal.getsignal(signal.SIGALRM)
    try:
        signal.signal(signal.SIGALRM, _alarm)
        signal.alarm(DETECTOR_TIMEOUT_SEG)
        return mod.scan(target)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, prev)


def _load_detector(name: str):
    path = DETECTORS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"detectors.{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"no se pudo cargar el detector {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "scan") or not hasattr(mod, "COVERED_OBLIGACIONES"):
        raise RuntimeError(f"{path}: el detector debe exponer scan() y COVERED_OBLIGACIONES")
    return mod


def _cargar_obligaciones() -> list[dict]:
    try:
        data = json.loads(OBLIGACIONES_JSON.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"ERROR: no se pudo cargar {OBLIGACIONES_JSON}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    if not isinstance(data, list):
        print(f"ERROR: {OBLIGACIONES_JSON} debe ser una lista", file=sys.stderr)
        raise SystemExit(1)
    return data


def _validar_techos(hallazgos: list[dict], por_id: dict[str, dict]) -> list[str]:
    """Un hallazgo jamás puede exceder el techo de su obligación."""
    problemas = []
    for h in hallazgos:
        ficha = por_id.get(h["obligacion_id"])
        if ficha is None:
            problemas.append(
                f"{h['detector']}: obligacion_id desconocido {h['obligacion_id']!r}"
            )
            continue
        techo_pack = ficha.get("techo_de_veredicto")
        if h["techo_de_veredicto"] != techo_pack:
            problemas.append(
                f"{h['detector']}: hallazgo con techo {h['techo_de_veredicto']!r} "
                f"pero la obligación {h['obligacion_id']} tiene techo {techo_pack!r}"
            )
    return problemas


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="scan.py", description=__doc__)
    parser.add_argument("repo", help="repo a auditar (directorio)")
    parser.add_argument("--json", metavar="salida.json", default=None,
                        help="escribir el JSON aquí; por defecto va a stdout")
    parser.add_argument("--include-secrets", action="store_true",
                        help="escanear explícitamente archivos cuyo contenido ES un "
                             "secreto (.env, *.pem, id_rsa*, credentials, .npmrc, netrc); "
                             "por defecto se excluyen (decisión D11 de la persona)")
    args = parser.parse_args(argv[1:])
    common.INCLUDE_SECRETS = args.include_secrets

    target = Path(args.repo).resolve()
    if not target.is_dir():
        print(f"ERROR: {target} no es un directorio", file=sys.stderr)
        return 2

    if args.json:
        out_path = Path(args.json).resolve()
        try:
            if out_path.is_relative_to(target):
                print(
                    "ERROR: el archivo de salida quedaría dentro del repo auditado "
                    "(read-only en el target).",
                    file=sys.stderr,
                )
                return 2
        except ValueError:
            pass

    obligaciones = _cargar_obligaciones()
    por_id = {f["id"]: f for f in obligaciones}

    # correr detectores
    hallazgos: list[dict] = []
    cobertura_por_detector: dict[str, list[str]] = {}
    metricas_por_detector: dict[str, dict[str, int]] = {}
    errores: list[str] = []
    # Un detector caído es visible en el PRIMER nivel del resumen, no solo en
    # la lista `errores`: `detectores_ejecutados` no puede leerse como
    # "cubierto" cuando algún detector no produjo nada.
    detectores_fallidos: list[str] = []
    for name in DETECTORS:
        try:
            mod = _load_detector(name)
        except Exception as exc:  # noqa: BLE001
            errores.append(f"{name}: no se pudo cargar: {exc}")
            detectores_fallidos.append(name)
            continue
        cobertura_por_detector[name] = sorted(mod.COVERED_OBLIGACIONES)
        try:
            common.reset_stats()
            hallazgos_mod = _scan_con_timeout(mod, target)
            metricas_por_detector[name] = dict(common.STATS)
        except _DetectorTimeout:
            errores.append(f"timeout: {name}")
            detectores_fallidos.append(name)
            continue
        except Exception as exc:  # noqa: BLE001
            errores.append(f"{name}: falló scan(): {exc}")
            detectores_fallidos.append(name)
            continue
        for h in hallazgos_mod:
            hd = h.to_dict() if hasattr(h, "to_dict") else dict(h)
            hallazgos.append(hd)

    # validar techos contra el pack
    problemas = _validar_techos(hallazgos, por_id)
    if problemas:
        for p in problemas:
            errores.append(f"INCOHERENCIA DE TECHO: {p}")

    # hallazgos ordenados: detector, archivo, línea
    hallazgos.sort(key=lambda h: (h.get("detector", ""), h.get("archivo", ""), h.get("linea", 0)))

    # resumen por detector / prioridad_revision / jurisdicción
    por_detector: dict[str, int] = {}
    por_prioridad: dict[str, int] = {}
    por_jurisdiccion: dict[str, int] = {}
    for h in hallazgos:
        por_detector[h["detector"]] = por_detector.get(h["detector"], 0) + 1
        prio = str(h.get("prioridad_revision", "MEDIA")).upper()
        por_prioridad[prio] = por_prioridad.get(prio, 0) + 1
        ficha = por_id.get(h["obligacion_id"], {})
        jur = ficha.get("jurisdiccion", "?")
        por_jurisdiccion[jur] = por_jurisdiccion.get(jur, 0) + 1

    # cobertura de obligaciones
    cubiertas = sorted({o for lst in cobertura_por_detector.values() for o in lst})
    ids_pack = sorted(por_id.keys())
    sin_detector = [o for o in ids_pack if o not in set(cubiertas)]
    con_detector_sin_hallazgo = [
        o for o in cubiertas
        if not any(h.get("obligacion_id") == o for h in hallazgos)
    ]
    con_hallazgo = sorted({h.get("obligacion_id") for h in hallazgos if h.get("obligacion_id")})

    marcado_obligaciones = {
        o: {
            "id": por_id[o]["id"],
            "jurisdiccion": por_id[o].get("jurisdiccion"),
            "articulo": por_id[o].get("articulo"),
            "determinismo": por_id[o].get("determinismo"),
            "determinismo_principal": por_id[o].get("determinismo_principal"),
            "techo_de_veredicto": por_id[o].get("techo_de_veredicto"),
            "responsable": por_id[o].get("responsable"),
        }
        for o in ids_pack
    }

    payload = {
        "schema_version": "1.0",
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pack_obligaciones": str(OBLIGACIONES_JSON.relative_to(SKILL_ROOT.parents[0])),
        "repo_auditado": str(target),
        "resumen": {
            "total_hallazgos": len(hallazgos),
            "por_detector": por_detector,
            "por_prioridad_revision": {s: por_prioridad.get(s, 0) for s in PRIORIDAD_ORDEN},
            "por_jurisdiccion": por_jurisdiccion,
            "detectores_ejecutados": len(cobertura_por_detector),
            "detectores_total": len(DETECTORS),
            "detectores_fallidos": detectores_fallidos,
            "errores_detectores": len(errores),
            "metricas_por_detector": metricas_por_detector,
        },
        "hallazgos": hallazgos,
        "cobertura_obligaciones": {
            "total_pack": len(ids_pack),
            "con_detector": cubiertas,
            "sin_detector": sin_detector,
            "con_detector_sin_hallazgo": con_detector_sin_hallazgo,
            "con_hallazgo": con_hallazgo,
            "por_detector": cobertura_por_detector,
        },
        "obligaciones": marcado_obligaciones,
        "errores": errores,
        "nota": (
            "Este output contiene HECHOS observables con archivo:línea. La skill "
            "nunca emite un veredicto global ni afirma cumplimiento/incumplimiento. "
            "Cada obligación lleva su techo_de_veredicto y determinismo declarados "
            "para que un subagente no pueda excederlos."
        ),
    }

    texto = json.dumps(payload, ensure_ascii=False, indent=2)

    # impresión humana a stdout
    print(f"repo auditado : {target}")
    print(f"pack          : {OBLIGACIONES_JSON}")
    print(f"detectores    : {len(cobertura_por_detector)}/{len(DETECTORS)}"
          + (f"  FALLIDOS: {', '.join(detectores_fallidos)}" if detectores_fallidos else ""))
    print(f"hallazgos     : {len(hallazgos)}  "
          f"(ALTA={por_prioridad.get('ALTA', 0)} MEDIA={por_prioridad.get('MEDIA', 0)} "
          f"BAJA={por_prioridad.get('BAJA', 0)} INFO={por_prioridad.get('INFO', 0)})")
    print("por detector  : " + ", ".join(f"{k}={v}" for k, v in sorted(por_detector.items())))
    print("por jurisdicción: " + ", ".join(f"{k}={v}" for k, v in sorted(por_jurisdiccion.items())))
    print(f"sin detector  : {len(sin_detector)} obligaciones sin cobertura "
          f"({', '.join(sin_detector)})")
    for name, metricas in sorted(metricas_por_detector.items()):
        if any(metricas.values()):
            print(f"métricas {name:16s}: " + ", ".join(f"{k}={v}" for k, v in sorted(metricas.items())))
    for e in errores:
        print(f"ERROR: {e}", file=sys.stderr)

    if args.json:
        out_path.write_text(texto, encoding="utf-8")
        print(f"escrito {out_path}")
    else:
        print(texto)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
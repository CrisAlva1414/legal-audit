#!/usr/bin/env python3
"""Helpers compartidos por los detectores de código de terceros (D1–D6).

Contrato común a todos los detectores:

    def scan(root: Path) -> list[Finding]
    class Finding                                    # dataclass (este módulo)
    COVERED_OBLIGACIONES: set[str]                   # ids de obligations.json
    def main(argv: list[str]) -> int                 # CLI (ver detector)

Principio de diseño (no negociable):
    - Un detector produce HECHOS observables con `archivo:línea`. Nunca
      afirma "cumple", "incumple" ni "vulnerabilidad".
    - Cada hallazgo hereda `techo_de_veredicto` de la obligación: un detector
      jamás puede subir el techo (doctrine.md:118-145).
    - Si la obligación es `NO-VERIFICABLE-ESTATICAMENTE`, el detector no
      emite nada para ella.
    - Los detectores son read-only: solo leen el repo auditado. Jamás
      escriben dentro de él.

Endurecimiento (security-reviewer, ALTA/MEDIA):
    - ALTA-1: el recorrido NO sigue symlinks y verifica contención en el
      root; un symlink que resuelva fuera del root se omite en silencio y se
      cuenta en `simlinks_omitidos`.
    - ALTA-2: la lectura tiene topes duros (2 MB por archivo, 10.000 chars
      por línea); un archivo/línea que exceda se trunca y se cuenta en
      `archivos_truncados`/`lineas_truncadas`.
    - MEDIA D11: los archivos cuyo contenido ES un secreto (.env, *.pem,
      id_rsa*, credentials, .npmrc, netrc, …) se excluyen del scan por
      defecto (`--include-secrets` los habilita), y el valor de un secreto
      que aparezca en evidencia/mensaje se reemplaza por `[REDACTED]`.
    - MEDIA D12: el campo de triage se llama `prioridad_revision`; cada
      hallazgo lleva `severidad_legal: null` (solo una persona la determina).

Solo stdlib. Sin red.
"""

from __future__ import annotations

import dataclasses
import json
import os
import re
from pathlib import Path

# --- ubicación de la skill ------------------------------------------------
# common.py vive en <raiz>/skills/legal-audit/scripts/detectors/common.py
SKILL_ROOT = Path(__file__).resolve().parents[2]
OBLIGACIONES_JSON = SKILL_ROOT / "references" / "obligations" / "obligations.json"

# --- recorrido del repo auditado -------------------------------------------
SKIP_PARTS = {
    ".git", "node_modules", "__pycache__", ".venv", ".tox", "dist", "build",
    ".next", ".nuxt", "coverage", ".mypy_cache", ".pytest_cache",
    "vendor", "pods", "target",
}


def _is_skipped_part(part: str) -> bool:
    """Parte de directorio que nunca se escanea (case-insensitive)."""
    p = part.lower()
    if p in SKIP_PARTS:
        return True
    return p.endswith((".dist-info", ".egg-info"))


# Extensiones textuales analizables. Detectar PII en binarios/empaquetados no
# es estático ni confiable: solo se escanea texto (docs/roadmap.md: texto plano).
SOURCE_EXTS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".vue", ".svelte", ".html", ".htm",
    ".css", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".env",
    ".sh", ".sql", ".go", ".java", ".rb", ".php", ".cs", ".md", ".txt",
}

# El propio paquete de la skill se excluye de cualquier auditoría: escanear el
# código de los detectores sería auto-referencial (sus tablas de patrones
# contienen las cadenas "email", "voice", etc. que disparan falsos positivos).
# El objeto auditado es código de terceros, no el propio producto.
_SKIP_SKILL_ROOT = SKILL_ROOT.resolve()

# --- límites duros de lectura (ALTA-2) ------------------------------------
MAX_FILE_BYTES = 2 * 1024 * 1024    # 2 MB por archivo
MAX_LINE_CHARS = 10_000             # 10.000 chars por línea

STATS = {
    "simlinks_omitidos": 0,       # symlinks que resuelven fuera del root
    "lineas_truncadas": 0,        # líneas cortadas por MAX_LINE_CHARS
    "archivos_truncados": 0,      # archivos cortados por MAX_FILE_BYTES
}


def reset_stats() -> None:
    for _k in STATS:
        STATS[_k] = 0


# --- archivos cuyo contenido ES el secreto (MEDIA D11) ----------------------
# Decisión de la persona (opción a + b): estos archivos no se escanean para
# PII por defecto. `--include-secrets` los habilita explícitamente.
SECRET_FILE_EXACT = {"credentials", "netrc", ".netrc", ".npmrc", ".pypirc"}
SECRET_FILE_PREFIXES = {".env", "id_rsa"}
SECRET_FILE_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".keystore"}
INCLUDE_SECRETS = False


def _is_secret_file(path: Path) -> bool:
    name = Path(path).name.lower()
    if name in SECRET_FILE_EXACT:
        return True
    if any(name.startswith(p) for p in SECRET_FILE_PREFIXES):
        return True
    if any(name.endswith(p) for p in SECRET_FILE_SUFFIXES):
        return True
    return False


def iter_source_files(root: Path, *, include_secrets: bool | None = None) -> list[Path]:
    """Archivos textuales del repo auditado, en orden, sin partes excluidas.

    - ALTA-1: `os.walk(followlinks=False)` nunca desciende por symlinks de
      directorio; un symlink de archivo solo se admite si resuelve DENTRO del
      root (`resolve().is_relative_to(root)`). Si resuelve fuera, se omite en
      silencio y suma a `STATS["simlinks_omitidos"]`.
    - Los archivos cuyo contenido ES un secreto (.env, *.pem, id_rsa*, …) se
      omiten salvo `include_secrets=True` (o `INCLUDE_SECRETS` global).
    """
    root = Path(root).resolve()
    if include_secrets is None:
        include_secrets = INCLUDE_SECRETS
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        kept: list[str] = []
        for d in dirnames:
            dp = os.path.join(dirpath, d)
            if os.path.islink(dp) or _is_skipped_part(d):
                continue
            kept.append(d)
        dirnames[:] = kept
        for fn in sorted(filenames):
            fp = Path(dirpath) / fn
            es_symlink = fp.is_symlink()
            if es_symlink:
                try:
                    resolved = fp.resolve()
                except (OSError, RuntimeError):
                    STATS["simlinks_omitidos"] += 1
                    continue
                if not resolved.is_relative_to(root):
                    STATS["simlinks_omitidos"] += 1
                    continue
            if not fp.is_file() or fp.suffix.lower() not in SOURCE_EXTS:
                continue
            parts = list(fp.parts)
            if es_symlink:
                parts += list(fp.resolve().parts)
            if any(_is_skipped_part(part) for part in parts):
                continue
            if _is_secret_file(fp) and not include_secrets:
                continue
            try:
                if fp.resolve().is_relative_to(_SKIP_SKILL_ROOT):
                    continue
            except (ValueError, OSError):
                pass
            out.append(fp)
    return sorted(out)


def read_text(path: Path) -> str:
    """Lee texto con topes duros (ALTA-2): 2 MB por archivo, 10K por línea.

    Exceder un tope trunca (no omite) y suma al estadístico
    `archivos_truncados` / `lineas_truncadas`. El contenido nunca se lanza a
    una regex completa sin límite.
    """
    try:
        size = path.stat().st_size
    except OSError:
        return ""
    if size > MAX_FILE_BYTES:
        try:
            with path.open("rb") as fh:
                data = fh.read(MAX_FILE_BYTES)
        except OSError:
            return ""
        STATS["archivos_truncados"] += 1
    else:
        try:
            data = path.read_bytes()
        except OSError:
            return ""
    text = data.decode("utf-8", errors="replace")
    if "\x00" in text:
        return ""
    if len(text) <= MAX_LINE_CHARS and "\n" not in text:
        return text
    out: list[str] = []
    for line in text.splitlines():
        if len(line) > MAX_LINE_CHARS:
            out.append(line[:MAX_LINE_CHARS])
            STATS["lineas_truncadas"] += 1
        else:
            out.append(line)
    return "\n".join(out)


# --- redacción de secretos (MEDIA D11) --------------------------------------
# El VALOR de un secreto nunca sale del detector: se conserva la clave y la
# línea, el valor se reemplaza por [REDACTED].
_SECRET_VALUE_RE = re.compile(
    r"AKIA[0-9A-Z]{16}"
    r"|sk-[A-Za-z0-9]{20,}"
    r"|ghp_[A-Za-z0-9]{20,}"
    r"|github_pat_[A-Za-z0-9_]{20,}"
    r"|-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"
    r"|(?:password|passwd|passphrase|api[_-]?key|access[_-]?key|secret|token|contrase[ñn]a|clave)\s*[=:]\s*\S+",
    re.IGNORECASE,
)


def _redact_value(match: re.Match) -> str:
    val = match.group(0)
    if val.lower().startswith("-----begin"):
        return "[REDACTED]"
    kv = re.match(r"^(.*?)(\s*[=:]\s*)(\S+)$", val, re.DOTALL)
    if kv:
        return kv.group(1) + kv.group(2) + "[REDACTED]"
    return "[REDACTED]"


def redact_secrets(text: str) -> str:
    if not text:
        return text
    return _SECRET_VALUE_RE.sub(_redact_value, text)


# --- Finding --------------------------------------------------------------
@dataclasses.dataclass(frozen=True)
class Finding:
    """Un hecho observable producido por un detector.

    `archivo` es relativo a la raíz auditada; `linea` es 1-based. Para hechos
    de AUSENCIA (no existe mecanismo X en el repo) no hay archivo:línea real:
    se usa `archivo = "."` y `linea = 0`, y el mensaje lo declara
    explícitamente ("no se ha encontrado ... en el repositorio").

    D12: `prioridad_revision` es triage TÉCNICO del detector
    (ALTA|MEDIA|BAJA|INFO); `severidad_legal` la determina una persona y es
    siempre `null` en la salida de la skill (doctrine.md, doc-triage).
    """

    detector: str
    obligacion_id: str
    archivo: str
    linea: int
    evidencia: str
    tipo: str                    # DETERMINISTA | SEMI (certeza del hecho)
    techo_de_veredicto: str      # heredado de obligations.json, nunca subido
    mensaje: str
    prioridad_revision: str = "MEDIA"   # ALTA|MEDIA|BAJA|INFO (triage técnico)
    severidad_legal: str | None = None  # null: solo una persona la determina
    confianza: str = "alta"      # alta|baja (heurística débil → baja)
    destino: str | None = None   # D1: "externo"|"interno"|"posible_externo"

    def __post_init__(self) -> None:
        # D11: el valor de un secreto jamás llega a evidencia ni mensaje.
        object.__setattr__(self, "evidencia", redact_secrets(self.evidencia))
        object.__setattr__(self, "mensaje", redact_secrets(self.mensaje))

    def to_dict(self) -> dict:
        base = dataclasses.asdict(self)
        base["ubicacion"] = f"{self.archivo}:{self.linea}"
        return base


def abs_to_rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return path.as_posix()


# --- pack de obligaciones --------------------------------------------------
_OBLIG_CACHE: dict[tuple[str, str], dict] = {}


def load_obligaciones(skill_root: Path | None = None) -> dict[str, dict]:
    """Obligations como {id: ficha}. Lee el pack propio de la skill (read-only)."""
    sr = Path(skill_root).resolve() if skill_root is not None else SKILL_ROOT
    key = (str(sr), "obligaciones")
    if key in _OBLIG_CACHE:
        return _OBLIG_CACHE[key]
    path = sr / "references" / "obligations" / "obligations.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RuntimeError(
            f"no se pudo cargar el pack de obligaciones {path}: {exc}"
        ) from exc
    if not isinstance(data, list):
        raise RuntimeError(f"{path}: se esperaba una lista de fichas")
    out = {ficha["id"]: ficha for ficha in data if isinstance(ficha, dict) and ficha.get("id")}
    _OBLIG_CACHE[key] = out
    return out


def obligacion_techo(obligacion_id: str, obligaciones: dict[str, dict] | None = None) -> str:
    obligaciones = obligaciones if obligaciones is not None else load_obligaciones()
    ficha = obligaciones.get(obligacion_id)
    if ficha is None:
        raise KeyError(f"obligacion_id {obligacion_id!r} no existe en obligations.json")
    return str(ficha["techo_de_veredicto"])


def make_finding(
    detector: str,
    obligacion_id: str,
    archivo: str,
    linea: int,
    evidencia: str,
    tipo: str,
    mensaje: str,
    prioridad_revision: str = "MEDIA",
    confianza: str = "alta",
    destino: str | None = None,
    obligaciones: dict[str, dict] | None = None,
) -> Finding:
    """Crea un Finding heredando el techo desde el pack (nunca lo sube).

    D12: el parámetro se llama `prioridad_revision` (triage técnico); la
    severidad jurídica no la asigna la skill.
    """
    techo = obligacion_techo(obligacion_id, obligaciones)
    return Finding(
        detector=detector,
        obligacion_id=obligacion_id,
        archivo=archivo,
        linea=linea,
        evidencia=evidencia,
        tipo=tipo,
        techo_de_veredicto=techo,
        mensaje=mensaje,
        prioridad_revision=prioridad_revision,
        confianza=confianza,
        destino=destino,
    )


# --- utilidades de regex ---------------------------------------------------
def compile_alt(patterns: list[str], flags: int = re.IGNORECASE) -> re.Pattern:
    """`patterns` son fragmentos OR de un mismo grupo no capturante."""
    body = "|".join(f"(?:{p})" for p in patterns)
    return re.compile(body, flags)


# --- CLI compartida ---------------------------------------------------------
def run_detector_cli(module, argv: list[str]) -> int:
    """main() genérico: `python3 <detector>.py <repo> [--json salida.json]
    [--include-secrets]`."""
    import sys

    global INCLUDE_SECRETS  # noqa: PLW0603 — flag del CLI, default False

    if len(argv) < 2:
        print(
            f"uso: python3 {Path(module.__file__).name} <repo-auditar> "
            "[--json salida.json] [--include-secrets]",
            file=sys.stderr,
        )
        return 2
    root = Path(argv[1])
    if not root.is_dir():
        print(f"ERROR: {root} no es un directorio", file=sys.stderr)
        return 2

    if "--include-secrets" in argv:
        INCLUDE_SECRETS = True

    try:
        hallazgos = module.scan(root)
    except Exception as exc:  # noqa: BLE001 — CLI debe reportar sin stacktrace
        print(f"ERROR ejecutando {module.__name__}: {exc}", file=sys.stderr)
        return 1

    payload = {
        "detector": module.__name__,
        "repo_auditado": str(root.resolve()),
        "total_hallazgos": len(hallazgos),
        "hallazgos": [h.to_dict() for h in hallazgos],
    }
    json_out = json.dumps(payload, ensure_ascii=False, indent=2)
    out_path: Path | None = None
    if "--json" in argv:
        i = argv.index("--json")
        if i + 1 < len(argv):
            out_path = Path(argv[i + 1])
    if out_path is None:
        print(json_out)
        return 0
    # Read-only respecto al repo auditado: el archivo de salida no puede caer
    # dentro del directorio auditado.
    target = Path(root).resolve()
    dest = Path(out_path).resolve()
    try:
        if dest.is_relative_to(target):
            print(
                "ERROR: el archivo de salida quedaría dentro del repo auditado "
                "(read-only en el target).",
                file=sys.stderr,
            )
            return 2
    except ValueError:
        pass
    out_path.write_text(json_out, encoding="utf-8")
    print(f"escrito {out_path} ({len(hallazgos)} hallazgos)")
    return 0
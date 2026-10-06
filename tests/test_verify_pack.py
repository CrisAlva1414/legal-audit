#!/usr/bin/env python3
"""Tests de evasión contra `verify_pack.py` (checks de integridad del pack).

Cada test reproduce una evasión que el security-reviewer demostró contra la
implementación vieja de `verify_pack.py`. El mismo archivo de tests corre
contra cualquiera de las dos implementaciones:

    python3 -m unittest discover -s tests            # contra la impl nueva
    VERIFY_PACK_PATH=/tmp/legal-audit-old/verify_pack.py \
        python3 -m unittest discover -s tests        # contra la vieja

Contra la vieja se espera que falle la mayoría (≥ 8/12): si un test pasa
contra la vieja, ese test no está probando nada.

Los tests construyen un fixture = copia mínima del pack real (SKILL.md +
references/) en un directorio temporal, aplican UNA mutación dirigida por
test, y llaman a los checks con ese fixture como raíz. No tocan el repo real.
"""

import contextlib
import hashlib
import importlib.util
import json
import os
import re
import shutil
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMPL = REPO_ROOT / "skills" / "legal-audit" / "scripts" / "verify_pack.py"
IMPL_PATH = Path(os.environ.get("VERIFY_PACK_PATH", str(DEFAULT_IMPL))).resolve()

# Archivos del pack real que se copian como base del fixture.
SKELETON = [
    "SKILL.md",
    "references/doctrine.md",
    "references/bibliography.md",
    "references/sources/gdpr.md",
    "references/sources/eprivacy.md",
    "references/sources/chile-21719.md",
    "references/sources/chile-eu-crosswalk.md",
]


_IMPL_TMP: tempfile.TemporaryDirectory | None = None


def _load_impl(path: Path):
    """Carga la implementación bajo prueba desde `path`.

    Ambos scripts calculan sus rutas con `Path(__file__).resolve().parents[N]`
    asumiendo vivir en `<root>/skills/legal-audit/scripts/verify_pack.py`.
    La vieja hace `parents[3]` y revienta si la cargamos desde un directorio
    plano (p. ej. `/tmp/legal-audit-old/`). Shim: copiar el script a un árbol
    temporal con esa profundidad y cargarlo desde ahí. Después, cada test
    apunta los checks al fixture con `_patch_paths`.
    """
    global _IMPL_TMP
    path = Path(path).resolve()
    _IMPL_TMP = tempfile.TemporaryDirectory(prefix="verify_pack_impl_shim_")
    shim_root = Path(_IMPL_TMP.name)
    target = shim_root / "skills" / "legal-audit" / "scripts" / "verify_pack.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    spec = importlib.util.spec_from_file_location("verify_pack_under_test", target)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


import atexit

atexit.register(lambda: _IMPL_TMP and _IMPL_TMP.cleanup())

IMPL = _load_impl(IMPL_PATH)


# --- helpers de fixture ------------------------------------------------------

def _patch_paths(mod, root: Path) -> None:
    """La impl vieja lee las rutas desde globals del módulo; la nueva usa el
    parámetro `root` pero no le hace daño que además queden apuntando al
    fixture (evita sorpresas si algún check mezcla ambas fuentes)."""
    mod.ROOT = root
    mod.REFERENCES = root / "skills" / "legal-audit" / "references"
    mod.SOURCES = root / "skills" / "legal-audit" / "references" / "sources"


@contextlib.contextmanager
def fixture():
    tmp = Path(tempfile.mkdtemp(prefix="verify_pack_test_"))
    root = tmp / "repo"
    for rel in SKELETON:
        src = REPO_ROOT / "skills" / "legal-audit" / rel
        dst = root / "skills" / "legal-audit" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    _patch_paths(IMPL, root)
    try:
        yield root
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def refs(root: Path) -> Path:
    return root / "skills" / "legal-audit" / "references"


def sources(root: Path) -> Path:
    return refs(root) / "sources"


def write_evasion_file(root: Path, content: str, name: str = "evasions.md") -> Path:
    """Crea un archivo de texto fuera de `sources/` con la frase bajo prueba."""
    p = refs(root) / name
    p.write_text(content, encoding="utf-8")
    return p


def _call(check, root: Path):
    """Llama al check con la API de la impl nueva (root explícito) y degrada a
    la API vieja (sin argumentos) si la firma no lo acepta."""
    try:
        return check(root)
    except TypeError:
        return check()


def _has_check(name: str) -> bool:
    return callable(getattr(IMPL, name, None))


def _mutate_field_in_article(text: str, heading: str, field_prefix: str,
                             new_value_line: str) -> str:
    """Reemplaza la primera línea de un campo dentro de la sección cuyo heading
    contiene `heading` (ej. `## GDPR Art. 25 —...`)."""
    start = text.index(heading)
    rest = text[start + len(heading):]
    m = re.search(r"^## GDPR ", rest, re.MULTILINE)
    end = start + len(heading) + m.start() if m else len(text)
    sec = text[start:end]
    lines = sec.splitlines(keepends=True)
    for i, ln in enumerate(lines):
        if ln.startswith(field_prefix):
            lines[i] = new_value_line + "\n"
            break
    else:
        raise AssertionError(f"campo {field_prefix!r} no encontrado en {heading!r}")
    return text[:start] + "".join(lines) + text[end:]


def _write_manifest(root: Path) -> Path:
    """Escribe un manifiesto válido (hashes correctos) para el fixture."""
    files = [
        "sources/gdpr.md",
        "sources/eprivacy.md",
        "sources/chile-21719.md",
        "sources/chile-eu-crosswalk.md",
        "doctrine.md",
        "bibliography.md",
    ]
    base = refs(root)
    lines = ["# SOURCES.sha256 — fixture de test"]
    for rel in files:
        p = base / rel
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        lines.append(f"{digest}  {rel}")
    manifest = sources(root) / "SOURCES.sha256"
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest


# --- helpers para check_obligations ------------------------------------------

def _valid_fichas(n: int = 33) -> list[dict]:
    """Fichas sintéticas válidas (determinismo del enum + techo coherente)."""
    dets = ["DETERMINISTA", "SEMI", "JUICIO", "NO-VERIFICABLE-ESTATICAMENTE"]
    techos = {
        "DETERMINISTA": "SATISFIED",
        "SEMI": "PARTIAL",
        "JUICIO": "PARTIAL",
        "NO-VERIFICABLE-ESTATICAMENTE": "NO_CONCLUIBLE_ESTATICAMENTE",
    }
    out = []
    for i in range(n):
        d = dets[i % len(dets)]
        out.append({
            "id": f"test-{i}",
            "jurisdiccion": "UE" if i % 2 == 0 else "CL",
            "articulo": f"Art. {i}",
            "titulo": f"Ficha sintética {i}",
            "cita": "cita sintetica " * 20,
            "operacionalizacion": "check sintetico",
            "determinismo": d,
            "caveat": "no aplica",
            "diferencia_con_gdpr": None,
            "techo_de_veredicto": techos[d],
            "responsable": "DETECTOR",
        })
    return out


def _write_obligations(root: Path, fichas: list[dict]) -> Path:
    path = refs(root) / "obligations" / "obligations.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(fichas, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return path


# --- tests -------------------------------------------------------------------

class EvasionTests(unittest.TestCase):
    """Un test por evasión demostrada por el security-reviewer."""

    def test_negation_shortcut(self):
        """'...cumple con la ley, no tengo dudas.' — el atajo de 'no'."""
        with fixture() as root:
            write_evasion_file(
                root,
                "## Estilo\n"
                "Esta implementacion cumple con la ley, no tengo dudas.\n",
            )
            _, flags = _call(IMPL.check_contamination, root)
        self.assertTrue(
            any("evasions.md:2" in f and "cumple con" in f for f in flags),
            f"esperaba flag por negación-laundered; flags={flags!r}",
        )

    def test_plural(self):
        """'cumple con las leyes' (plural)."""
        with fixture() as root:
            write_evasion_file(
                root,
                "## Estilo\n"
                "La solucion cumple con las leyes aplicables.\n",
            )
            _, flags = _call(IMPL.check_contamination, root)
        self.assertTrue(
            any("evasions.md:2" in f and "cumple con" in f for f in flags),
            f"esperaba flag por plural; flags={flags!r}",
        )

    def test_no_accent(self):
        """'Garantiza anonimizacion' — sin tilde no debe esquivar la regla."""
        with fixture() as root:
            write_evasion_file(
                root,
                "## Estilo\n"
                "Garantiza anonimizacion de los datos.\n",
            )
            _, flags = _call(IMPL.check_contamination, root)
        self.assertTrue(
            any("evasions.md:2" in f and "anonimiza" in f for f in flags),
            f"esperaba flag sin acento; flags={flags!r}",
        )

    def test_multiline_phrase(self):
        """Frase prohibida partida en dos líneas (ventana de contexto).

        Se usa la forma plural ('las leyes') para aislar la feature de ventana:
        el singular ('la ley') lo cubre test_negation_shortcut, y NO matchea
        hoy por el bug del regex `leyes?` reportado en verify_pack.py (el
        patrón exige 'leye'/'leyes', nunca 'ley').
        """
        with fixture() as root:
            write_evasion_file(
                root,
                "## Estilo\n"
                "La implementacion cumple con\n"
                "las leyes aplicables, sin objeciones.\n",
            )
            _, flags = _call(IMPL.check_contamination, root)
        self.assertTrue(
            any("evasions.md:2" in f and "cumple con" in f for f in flags),
            f"esperaba flag por frase partida; flags={flags!r}",
        )

    def test_forbidden_outside_context(self):
        """'La auditoría pasó; k≥5 es anónimo' fuera de doctrina (en Estilo)."""
        with fixture() as root:
            write_evasion_file(
                root,
                "## Estilo\n"
                "La auditoría pasó; k≥5 es anónimo.\n",
            )
            _, flags = _call(IMPL.check_contamination, root)
        self.assertTrue(
            any("evasions.md:2" in f and ("auditoria" in f or "anonimo" in f)
                for f in flags),
            f"esperaba flag fuera de contexto doctrinal; flags={flags!r}",
        )

    def test_file_not_in_manifest(self):
        """Un archivo extra en sources/ es activo desprotegido (T2)."""
        if not _has_check("check_hash"):
            self.fail("implementación sin check_hash: no puede detectar extra")
        with fixture() as root:
            _write_manifest(root)
            extra = sources(root) / "sneaky.md"
            extra.write_text("fuente agregada sin hash\n", encoding="utf-8")
            failures = _call(IMPL.check_hash, root)
        self.assertTrue(
            any("NO LISTADO" in f and "sneaky.md" in f for f in failures),
            f"esperaba flag por archivo fuera del manifiesto; failures={failures!r}",
        )

    def test_determinism_enum(self):
        """`Determinismo: INVENTADO` — valor fuera del enum."""
        with fixture() as root:
            gdpr = sources(root) / "gdpr.md"
            text = gdpr.read_text(encoding="utf-8")
            text = _mutate_field_in_article(
                text,
                "## GDPR Art. 25 — Protección por diseño y por defecto",
                "- **Determinismo:**",
                "- **Determinismo:** INVENTADO",
            )
            gdpr.write_text(text, encoding="utf-8")
            failures = _call(IMPL.check_fields, root)
        self.assertTrue(
            any("INVENTADO" in f and "enum" in f for f in failures),
            f"esperaba flag por enum inválido; failures={failures!r}",
        )

    def test_determinism_art25(self):
        """Art. 25 a DETERMINISTA habilita SATISFIED sobre JUICIO (T2→T5)."""
        with fixture() as root:
            gdpr = sources(root) / "gdpr.md"
            text = gdpr.read_text(encoding="utf-8")
            text = _mutate_field_in_article(
                text,
                "## GDPR Art. 25 — Protección por diseño y por defecto",
                "- **Determinismo:**",
                "- **Determinismo:** DETERMINISTA",
            )
            gdpr.write_text(text, encoding="utf-8")
            failures = _call(IMPL.check_fields, root)
        self.assertTrue(
            any("incoherente con doctrina" in f for f in failures),
            f"esperaba flag por subir JUICIO→DETERMINISTA; failures={failures!r}",
        )

    def test_empty_citation(self):
        """`**Cita:** (vacío)` — una cita placeholder no es evidencia."""
        with fixture() as root:
            gdpr = sources(root) / "gdpr.md"
            text = gdpr.read_text(encoding="utf-8")
            text = _mutate_field_in_article(
                text,
                "## GDPR Art. 25 — Protección por diseño y por defecto",
                "- **Texto/cita:**",
                "- **Texto/cita:** (vacío)",
            )
            gdpr.write_text(text, encoding="utf-8")
            failures = _call(IMPL.check_fields, root)
        self.assertTrue(
            any("demasiado corta" in f and "corto" in f.lower()
                or "demasiado corta" in f for f in failures),
            f"esperaba flag por cita vacía; failures={failures!r}",
        )

    def test_article_allowlist(self):
        """`Art. 99` en columna UE del crosswalk — fuera de la allowlist."""
        with fixture() as root:
            xw = sources(root) / "chile-eu-crosswalk.md"
            text = xw.read_text(encoding="utf-8")
            old = "| 1 | Base legal | Art. 6 (6 bases) |"
            new = "| 1 | Base legal | Art. 99 (6 bases) |"
            self.assertIn(old, text)
            xw.write_text(text.replace(old, new), encoding="utf-8")
            failures = _call(IMPL.check_crosswalk, root)
        self.assertTrue(
            any("allowlist" in f and "99" in f for f in failures),
            f"esperaba flag por artículo fuera de allowlist; failures={failures!r}",
        )

    def test_invalid_root(self):
        """Carpeta sin skills/legal-audit/SKILL.md → ROOT inválido (no opera)."""
        if not _has_check("resolve_root"):
            self.fail("implementación sin resolve_root: no puede validar ROOT")
        with tempfile.TemporaryDirectory(prefix="verify_pack_badroot_") as tmp:
            bad = Path(tmp) / "no-skill"
            bad.mkdir()
            (bad / "README.md").write_text("no es el repo\n", encoding="utf-8")
            with self.assertRaises(IMPL.RootError):
                IMPL.resolve_root(bad)

    def test_hash_mismatch(self):
        """Un archivo del manifiesto alterado debe fallar `check_hash`."""
        if not _has_check("check_hash"):
            self.fail("implementación sin check_hash: no puede detectar mutación")
        with fixture() as root:
            _write_manifest(root)
            gdpr = sources(root) / "gdpr.md"
            with gdpr.open("a", encoding="utf-8") as fh:
                fh.write("\n--- mutación ---\n")
            failures = _call(IMPL.check_hash, root)
        self.assertTrue(
            any("HASH" in f and "gdpr.md" in f for f in failures),
            f"esperaba flag por hash adulterado; failures={failures!r}",
        )


class ObligationsTests(unittest.TestCase):
    """Checks de `check_obligations` sobre `references/obligations/`.

    El control nuclear: un `JUICIO` (o `NO-VERIFICABLE-ESTATICAMENTE`)
    jamás puede declarar `techo_de_veredicto == SATISFIED`. El objetivo de
    estos tests es que una edición a mano de obligations.json que intente
    "subir" un techo sea detectada igual que una generación rota.
    """

    def test_techo_mapping_enum(self):
        """Techo correcto para cada valor del enum (doctrine.md:118-145)."""
        expected = {
            "DETERMINISTA": "SATISFIED",
            "SEMI": "PARTIAL",
            "JUICIO": "PARTIAL",
            "NO-VERIFICABLE-ESTATICAMENTE": "NO_CONCLUIBLE_ESTATICAMENTE",
        }
        for det, techo in expected.items():
            self.assertEqual(
                IMPL.DETERMINISM_TECHO[det], techo,
                f"techo mal mapeado para {det}",
            )
            self.assertEqual(
                IMPL._primary_determinism(det), det,
                f"el propio enum no se reconoce a sí mismo: {det}",
            )

    def test_juicio_techo_satisfied_fails(self):
        """Ficha `JUICIO` con `techo SATISFIED` → falla el control nuclear."""
        if not _has_check("check_obligations"):
            self.fail("implementación sin check_obligations")
        with fixture() as root:
            fichas = _valid_fichas()
            fichas[0]["determinismo"] = "JUICIO"
            fichas[0]["techo_de_veredicto"] = "SATISFIED"
            _write_obligations(root, fichas)
            failures = _call(IMPL.check_obligations, root)
        self.assertTrue(
            any("CONTROL NUCLEAR" in f for f in failures),
            f"esperaba flag por JUICIO->SATISFIED; failures={failures!r}",
        )

    def test_determinismo_inventado_fails(self):
        """`determinismo` fuera del enum → falla."""
        if not _has_check("check_obligations"):
            self.fail("implementación sin check_obligations")
        with fixture() as root:
            fichas = _valid_fichas()
            fichas[0]["determinismo"] = "INVENTADO"
            _write_obligations(root, fichas)
            failures = _call(IMPL.check_obligations, root)
        self.assertTrue(
            any("enum" in f and "INVENTADO" in f for f in failures),
            f"esperaba flag por determinismo inventado; failures={failures!r}",
        )

    def test_id_duplicado_fails(self):
        """Dos fichas con el mismo `id` → falla."""
        if not _has_check("check_obligations"):
            self.fail("implementación sin check_obligations")
        with fixture() as root:
            fichas = _valid_fichas()
            fichas[1]["id"] = fichas[0]["id"]
            _write_obligations(root, fichas)
            failures = _call(IMPL.check_obligations, root)
        self.assertTrue(
            any("duplicado" in f for f in failures),
            f"esperaba flag por id duplicado; failures={failures!r}",
        )

    def test_obligations_ausente_fails(self):
        """obligations.json ausente → falla, no pass silencioso."""
        if not _has_check("check_obligations"):
            self.fail("implementación sin check_obligations")
        with fixture() as root:
            # El fixture arranca sin references/obligations/obligations.json
            failures = _call(IMPL.check_obligations, root)
        self.assertTrue(
            any("FALTA" in f or "no existe" in f for f in failures),
            f"esperaba flag por obligations.json ausente; failures={failures!r}",
        )

    def test_obligations_truncado_fails(self):
        """obligations.json con < 30 fichas (truncado) → falla."""
        if not _has_check("check_obligations"):
            self.fail("implementación sin check_obligations")
        with fixture() as root:
            _write_obligations(root, _valid_fichas(3))
            failures = _call(IMPL.check_obligations, root)
        self.assertTrue(
            any("mínimo" in f or "truncado" in f for f in failures),
            f"esperaba flag por JSON truncado; failures={failures!r}",
        )

    def test_obligations_valido_pasa(self):
        """Pack sintético válido (33 fichas coherentes) → sin fallos."""
        if not _has_check("check_obligations"):
            self.fail("implementación sin check_obligations")
        with fixture() as root:
            _write_obligations(root, _valid_fichas())
            failures = _call(IMPL.check_obligations, root)
        self.assertEqual(failures, [])

    def test_obligations_real_pack_pasa(self):
        """El obligations.json generado por el builder pasa el check."""
        if not _has_check("check_obligations"):
            self.fail("implementación sin check_obligations")
        src = REPO_ROOT / "skills" / "legal-audit" / "references" / "obligations" / "obligations.json"
        if not src.is_file():
            self.fail("falta obligations.json generado (correr build_obligations.py)")
        with fixture() as root:
            dst = refs(root) / "obligations" / "obligations.json"
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            failures = _call(IMPL.check_obligations, root)
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
#!/usr/bin/env python3
"""Tests de los 6 detectores de legal-audit contra `tests/fixtures/`.

Cubre:
- un caso positivo y uno negativo por detector (12 tests);
- el blindaje ePrivacy (T-categoría): una anomalía de cookies se reporta
  como ePrivacy Art. 5(3), NUNCA como Art. 6 GDPR;
- el techo de veredicto (T-techos): ningún hallazgo puede superar el
  `techo_de_veredicto` de su obligación en obligations.json;
- read-only (T-read-only): scan.py completo no crea ni modifica archivos
  en el árbol auditado (lista de archivos + mtime);
- lenguaje: ningún mensaje de hallazgo contiene las palabras prohibidas
  "incumplimiento", "vulnerable", "cumple con la ley".

Correr: python3 -m unittest discover -s tests
Solo stdlib. Sin red.
"""

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DETECTORS_DIR = REPO_ROOT / "skills" / "legal-audit" / "scripts" / "detectors"
SCAN_PY = REPO_ROOT / "skills" / "legal-audit" / "scripts" / "scan.py"
OBLIGACIONES_JSON = (
    REPO_ROOT / "skills" / "legal-audit" / "references" / "obligations" / "obligations.json"
)
FIXTURES = REPO_ROOT / "tests" / "fixtures"

DETECTORS = [
    "pii_sinks",
    "consent_flow",
    "dsar_endpoints",
    "pii_in_logs",
    "security_config",
    "minors_and_voice",
]

# Orden de «poder» de los techos de veredicto (decreto decreciente).
TECHO_RANK = {
    "SATISFIED": 3,
    "PARTIAL": 2,
    "NO_CONCLUIBLE_ESTATICAMENTE": 1,
}

FORBIDDEN_WORDS = ("incumplimiento", "vulnerable", "cumple con la ley")

_MODULES: dict[str, object] = {}


def _load_detector(name: str):
    """Carga un detector por path (como scan.py), cacheado por test."""
    if name in _MODULES:
        return _MODULES[name]
    path = DETECTORS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"detectors.{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"no se pudo cargar {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _MODULES[name] = mod
    return mod


def _scan(name: str, root: Path) -> list:
    """findings del detector `name` sobre `root` (Finding objects)."""
    return _load_detector(name).scan(root)


def _obligaciones() -> dict[str, dict]:
    data = json.loads(OBLIGACIONES_JSON.read_text(encoding="utf-8"))
    return {f["id"]: f for f in data if isinstance(f, dict) and f.get("id")}


def _all_fixture_findings() -> dict[str, list]:
    """Todos los hallazgos de los 6 detectores contra tests/fixtures/."""
    return {name: _scan(name, FIXTURES) for name in DETECTORS}


def _snapshot_tree(root: Path) -> dict[str, tuple[int, int]]:
    """{(relpath): (mtime_ns, size)} de todo archivo bajo `root`."""
    out: dict[str, tuple[int, int]] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            st = p.stat()
            out[str(p.relative_to(root))] = (st.st_mtime_ns, st.st_size)
    return out


class DetectorFixtureTests(unittest.TestCase):
    """Caso positivo y negativo por detector (2 × 6 = 12)."""

    def _pos(self, name: str) -> list:
        findings = _scan(name, FIXTURES / name / "positive")
        return findings

    def _neg(self, name: str) -> list:
        return _scan(name, FIXTURES / name / "negative")

    # --- pii_sinks -------------------------------------------------------
    def test_pii_sinks_positive(self):
        """El fixture positivo de pii_sinks cruza email → sink externo."""
        findings = self._pos("pii_sinks")
        self.assertTrue(findings, "pii_sinks/positive sin hallazgos")
        cruce = [
            h for h in findings
            if h.destino == "externo" and "correo electrónico" in h.mensaje
        ]
        self.assertTrue(cruce, f"sin cruce email→externo; hallazgos={findings!r}")

    def test_pii_sinks_negative(self):
        """pii_sinks/negative: ningún campo declarado fluye a un sink."""
        findings = self._neg("pii_sinks")
        self.assertFalse(
            any("se detectó el campo" in h.mensaje for h in findings),
            f"esperaba 0 cruces campo→sink; hallazgos={findings!r}",
        )

    # --- consent_flow -----------------------------------------------------
    def test_consent_flow_positive(self):
        """Script de terceros antes del consentimiento + banner sin rechazo."""
        findings = self._pos("consent_flow")
        self.assertTrue(findings, "consent_flow/positive sin hallazgos")
        self.assertTrue(
            any("script de terceros" in h.mensaje for h in findings),
            f"falta hallazgo de script de terceros; {findings!r}",
        )

    def test_consent_flow_negative(self):
        """Consentimiento declarado antes del tracker → sin hallazgos."""
        self.assertEqual(self._neg("consent_flow"), [])

    # --- dsar_endpoints ---------------------------------------------------
    def test_dsar_endpoints_positive(self):
        """Endpoint DSAR presente se reporta como mecanismo encontrado."""
        findings = self._pos("dsar_endpoints")
        self.assertTrue(findings, "dsar_endpoints/positive sin hallazgos")
        self.assertTrue(
            any("se encontró mecanismo o ruta" in h.mensaje for h in findings),
            f"sin hallazgo de presencia; {findings!r}",
        )

    def test_dsar_endpoints_negative(self):
        """Sin rutas DSAR → solo hechos de ausencia, nunca presencia."""
        findings = self._neg("dsar_endpoints")
        self.assertTrue(findings, "esperaba hechos de ausencia (f:0)")
        self.assertFalse(
            any("se encontró mecanismo" in h.mensaje for h in findings),
            f"no debería reportar presencia; {findings!r}",
        )

    # --- pii_in_logs ------------------------------------------------------
    def test_pii_in_logs_positive(self):
        """PII en log/print se reporta."""
        findings = self._pos("pii_in_logs")
        self.assertTrue(findings, "pii_in_logs/positive sin hallazgos")

    def test_pii_in_logs_negative(self):
        self.assertEqual(self._neg("pii_in_logs"), [])

    # --- security_config ---------------------------------------------------
    def test_security_config_positive(self):
        """verify=False y CORS permiso (B3) se reportan."""
        findings = self._pos("security_config")
        self.assertTrue(
            any("verificación TLS" in h.mensaje for h in findings),
            f"falta hallazgo verify=False; {findings!r}",
        )
        self.assertTrue(
            any("CORS" in h.mensaje for h in findings),
            f"falta hallazgo CORS (B3); {findings!r}",
        )

    def test_security_config_negative(self):
        self.assertEqual(self._neg("security_config"), [])

    def test_security_config_no_headers_no_exception(self):
        """Regresión BUG-scope: un repo con entradas HTTP candidatas pero sin
        cabeceras de seguridad no debe lanzar NameError (comprehension en
        Python 3 no expone `h` fuera de su scope). Debe emitir el hecho de
        ausencia mapeado a gdpr-art-25 con techo PARTIAL. Fallaba con el bug.
        """
        root = FIXTURES / "security_config" / "no_headers"
        findings = _scan("security_config", root)  # no debe lanzar
        self.assertTrue(findings, "esperaba hallazgo de cabeceras ausentes")
        ausencia = [h for h in findings if "cabecera de seguridad" in h.mensaje]
        self.assertTrue(
            ausencia,
            f"falta el hecho de ausencia de cabeceras; hallazgos={findings!r}",
        )
        for h in ausencia:
            self.assertEqual(
                h.obligacion_id, "gdpr-art-25",
                "la ausencia de cabeceras por defecto mapea a Art. 25(2)",
            )
            self.assertEqual(
                h.techo_de_veredicto, "PARTIAL",
                "Art. 25(2) es JUICIO → techo PARTIAL, nunca SATISFIED",
            )

    # --- minors_and_voice -------------------------------------------------
    def test_minors_and_voice_positive(self):
        findings = self._pos("minors_and_voice")
        self.assertTrue(findings, "minors_and_voice/positive sin hallazgos")

    def test_minors_and_voice_negative(self):
        self.assertEqual(self._neg("minors_and_voice"), [])


class CategoriaTests(unittest.TestCase):
    """T-categoría: una anomalía de cookies es ePrivacy Art. 5(3), nunca Art. 6."""

    def test_third_party_script_es_eprivacy_no_gdpr_art6(self):
        findings = _scan("consent_flow", FIXTURES / "consent_flow" / "positive")
        scripts = [h for h in findings if "script de terceros" in h.mensaje]
        self.assertTrue(scripts, "no se reportó el script de terceros del fixture")
        for h in scripts:
            self.assertEqual(
                h.obligacion_id, "eprivacy-art-5-3",
                "script de terceros antes del consentimiento debe mapear a ePrivacy Art. 5(3)",
            )
        # Blindaje: ningún hallazgo de consent_flow (ni de ningún detector)
        # puede usar un id de Art. 6 GDPR para una anomalía de cookies.
        todos = _all_fixture_findings()
        for det, findings in todos.items():
            self.assertFalse(
                any(h.obligacion_id == "gdpr-art-6" for h in findings),
                f"detector {det} emitió un hallazgo con id de Art. 6 GDPR",
            )


class TechosTests(unittest.TestCase):
    """T-techos: ningún hallazgo supera el techo de su obligación."""

    def test_ningun_hallazgo_sube_el_techo(self):
        obligaciones = _obligaciones()
        todos = _all_fixture_findings()
        self.assertTrue(
            any(todos.values()),
            "no se generaron hallazgos contra fixtures: el test no prueba nada",
        )
        errores = []
        for det, findings in todos.items():
            for h in findings:
                ficha = obligaciones.get(h.obligacion_id)
                if ficha is None:
                    errores.append(f"{det}: obligacion_id desconocido {h.obligacion_id!r}")
                    continue
                techo_pack = ficha.get("techo_de_veredicto")
                if h.techo_de_veredicto != techo_pack:
                    rank_f = TECHO_RANK.get(h.techo_de_veredicto)
                    rank_p = TECHO_RANK.get(techo_pack)
                    if rank_f is None or rank_p is None or rank_f > rank_p:
                        errores.append(
                            f"{det}: hallazgo con techo {h.techo_de_veredicto!r} "
                            f"supera el techo {techo_pack!r} de {h.obligacion_id}"
                        )
        self.assertEqual(errores, [])


class ReadOnlyTests(unittest.TestCase):
    """T-read-only: scan.py no crea ni modifica archivos en el árbol auditado."""

    def test_scan_no_modifica_el_arbol(self):
        before = _snapshot_tree(FIXTURES)
        proc = subprocess.run(
            [sys.executable, str(SCAN_PY), str(FIXTURES)],
            capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(proc.returncode, 0, f"scan.py falló:\n{proc.stderr}")
        after = _snapshot_tree(FIXTURES)
        self.assertEqual(
            sorted(after),
            sorted(before),
            "scan.py creó o eliminó archivos en el árbol auditado",
        )
        for rel in before:
            self.assertEqual(
                after[rel], before[rel],
                f"scan.py modificó {rel} (mtime/tamaño)",
            )


class LenguajeTests(unittest.TestCase):
    """Ningún mensaje de hallazgo contiene palabras de veredicto prohibidas."""

    def test_mensajes_sin_palabras_prohibidas(self):
        todos = _all_fixture_findings()
        violaciones = []
        for det, findings in todos.items():
            for h in findings:
                texto = f"{h.mensaje} | {h.evidencia}"
                for word in FORBIDDEN_WORDS:
                    if word in texto:
                        violaciones.append(f"{det}: '{word}' en {h.archivo}:{h.linea}")
        self.assertEqual(violaciones, [])


if __name__ == "__main__":
    unittest.main()
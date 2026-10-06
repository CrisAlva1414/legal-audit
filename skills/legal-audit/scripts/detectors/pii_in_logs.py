#!/usr/bin/env python3
"""D4 — pii_in_logs.py · DETERMINISTA → Art. 5(1)(f) + Art. 32

Datos personales en logs y configuración de niveles de log.

Hechos emitidos:
  - PII en sentencia de log (mensaje, formato, objeto serializado) → Art. 32
    (hecho de código: el dato alcanza el log sin redacción).
  - PII a nivel `debug`/`trace`/`verbose`, o `level=DEBUG` explícito en
    configuración de logging fuera de tests → Art. 5 (hecho de configuración:
    el repositorio no garantiza que ese detalle quede fuera de producción).

Nunca se emite "vulnerabilidad": solo "se detectó PII en la sentencia de log
en archivo:línea". Read-only. Solo stdlib. Sin red.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    abs_to_rel,
    compile_alt,
    iter_source_files,
    load_obligaciones,
    make_finding,
    read_text,
    run_detector_cli,
)

DETECTOR = "pii_in_logs"
COVERED_OBLIGACIONES = {"gdpr-art-5", "gdpr-art-32"}

LOG_CALL_RE = re.compile(
    r"(?P<caller>logger|logging|log|console|logger2|audit)\s*\.\s*"
    r"(?P<level>debug|trace|verbose|info|warn|warning|error|critical|exception|fatal)"
    r"\s*\(",
    re.IGNORECASE,
)
_PRINT_RE = re.compile(r"\bprint\s*\(")
_WRITE_RE = re.compile(r"\b(?:sys\.stdout|sys\.stderr|stdout|stderr)\.(?:\w+\.)?write\s*\(")
_LOGGER_GET_RE = compile_alt([
    r"logging\.getLogger", r"getLogger\(", r"logger\s*=\s*log", r"log\s*=\s*logging",
])
_LEVEL_DEBUG_RE = compile_alt([
    r"basicConfig\s*\([^)]*\bDEBUG\b", r"level\s*=\s*logging\.DEBUG",
    r"level\s*=\s*\bDEBUG\b", r"LOG_LEVEL\s*[=:]\s*[\"']?(?:DEBUG|TRACE)",
    r"SetLogLevel\s*\(\s*[\"']?debug", r"setLevel\s*\(\s*logging\.DEBUG",
    r"setLevel\s*\(\s*[\"']?debug",
])

# PII buscada dentro de la ventana de la llamada de log.
_PII_TOKEN_RE = compile_alt([
    r"e-?mail|correo", r"phone|telefono|tel[eé]fono|celular|whatsapp",
    r"first_?name|last_?name|full_?name|nombre|apellido",
    r"birth(?:date|_date|day)?|fecha_?nacimiento|\bdob\b",
    r"national_?id|passport|documento|\bdni\b|\brut\b|cedula|c[eé]dula|id_?number|ssn",
    r"ip_?address|remote_?addr|client_?ip|source_?ip|\bip\b",
    r"device_?id|user_?agent|imei|idfa|ad_?id",
    r"cookie_?id|session_?id|fingerprint|access_?token|auth_?token|api_?key|secret",
    r"location|geolocation|latitude|longitude|\bgps\b",
    r"voice|audio|speech|transcript|grabacion|grabaci[oó]n|llamada|embedding|biometric|biometr[íi]a",
    r"password|passwd|contrase[ñn]a|clave\b",
])
# objeto potencialmente con PII serializado en el log
_DUMPED_OBJ_RE = compile_alt([
    r"str\s*\(\s*(?P<o>[A-Za-z_]\w*)\s*\)", r"f\"\{(?P<o2>[A-Za-z_]\w*)\}\"",
    r"f'\{(?P<o3>[A-Za-z_]\w*)\}'", r"repr\s*\(\s*(?P<o4>[A-Za-z_]\w*)\s*\)",
    r"json\.dumps\s*\(\s*(?P<o5>[A-Za-z_]\w*)", r"JSON\.stringify\s*\(\s*(?P<o6>[A-Za-z_]\w*)",
])
_OBJ_LIKE_RE = compile_alt([
    r"\b(user|person|profile|record|customer|patient|client|contact|subscriber|"
    r"account|order|request|response|payload|data|item|body)\b",
])
_MODEL_CLASS_RE = compile_alt([
    r"class\s+(User|Person|Profile|Customer|Patient|Client|Contact|Subscriber|Account|Order)\b",
])


def _call_window(lines: list[str], lineno: int) -> str:
    """Ventana de una llamada de log: desde la línea del call hasta 3 después."""
    end = min(len(lines), lineno + 3)
    return "\n".join(lines[lineno - 1:end])


def scan(root: Path) -> list[Finding]:
    root = Path(root)
    obligaciones = load_obligaciones()
    hallazgos: list[Finding] = []
    # modelos con PII conocidos en el repo (para objetividad de `str(user)`)
    modelos_con_pii = set()

    files = iter_source_files(root)
    for p in files:
        text = read_text(p)
        for m in _MODEL_CLASS_RE.finditer(text):
            modelos_con_pii.add(m.group(0).split()[-1].lower())

    for p in files:
        rel = abs_to_rel(root, p)
        lines = read_text(p).splitlines()
        is_test = "test" in rel.lower() or "spec" in rel.lower() or "/tests/" in "/"+rel+"/"

        for lineno, line in enumerate(lines, 1):
            # nivel = debug/trace/verbose → hecho de configuración (Art. 5)
            call = LOG_CALL_RE.search(line)
            if call:
                level = call.group("level").lower()
                window = _call_window(lines, lineno)
                pii_name = _PII_TOKEN_RE.search(window)
                obj_match = _DUMPED_OBJ_RE.search(window)
                serialized_objs: list[str] = []
                if obj_match:
                    serialized_objs = [g for g in obj_match.groups() if g]
                obj_like = _OBJ_LIKE_RE.search(window)

                if pii_name or serialized_objs or (obj_like and obj_like.group(0).lower() in modelos_con_pii):
                    objeto = serialized_objs[0] if serialized_objs else (obj_like.group(0) if obj_like else "")
                    confianza = "alta" if pii_name else (
                        "alta" if objeto.lower() in modelos_con_pii else "baja"
                    )
                    if level in ("debug", "trace", "verbose"):
                        ob = "gdpr-art-5"
                        mensaje = (
                            f"se detectó PII en log de nivel {level} en {rel}:{lineno}"
                            + (f" (token `{pii_name.group(0)}`)" if pii_name else f" (objeto `{objeto}` serializado)")
                            + "; el detalle puede quedar desactivado en producción y el repositorio no lo garantiza (hecho de configuración)"
                        )
                        sev = "MEDIA"
                    else:
                        ob = "gdpr-art-32"
                        mensaje = (
                            f"se detectó PII en sentencia de log ({call.group('level')}) en {rel}:{lineno}"
                            + (f" — token `{pii_name.group(0)}`" if pii_name else f" — objeto `{objeto}` serializado")
                        )
                        sev = "ALTA" if pii_name and re.search(r"voice|audio|biometric|embedding|password|passwd|secret|token|api_?key", window, re.IGNORECASE) else "MEDIA"
                    hallazgos.append(make_finding(
                        detector=DETECTOR, obligacion_id=ob,
                        archivo=rel, linea=lineno,
                        evidencia=line.strip()[:150],
                        tipo="DETERMINISTA", mensaje=mensaje,
                        prioridad_revision=sev, confianza=confianza,
                        obligaciones=obligaciones,
                    ))
            elif _PRINT_RE.search(line) or _WRITE_RE.search(line):
                window = _call_window(lines, lineno)
                pii_name = _PII_TOKEN_RE.search(window)
                obj_match = _DUMPED_OBJ_RE.search(window)
                serialized_objs = [g for g in obj_match.groups() if g] if obj_match else []
                obj_like = _OBJ_LIKE_RE.search(window)
                if pii_name or serialized_objs or (obj_like and obj_like.group(0).lower() in modelos_con_pii):
                    objeto = serialized_objs[0] if serialized_objs else (obj_like.group(0) if obj_like else "")
                    confianza = "alta" if pii_name else (
                        "alta" if objeto.lower() in modelos_con_pii else "baja"
                    )
                    hallazgos.append(make_finding(
                        detector=DETECTOR, obligacion_id="gdpr-art-32",
                        archivo=rel, linea=lineno,
                        evidencia=line.strip()[:150],
                        tipo="DETERMINISTA",
                        mensaje=(
                            f"se detectó PII en salida de consola/print en {rel}:{lineno}"
                            + (f" (token `{pii_name.group(0)}`)" if pii_name else f" (objeto `{objeto}`)")
                        ),
                        prioridad_revision="MEDIA", confianza=confianza,
                        obligaciones=obligaciones,
                    ))

        # nivel DEBUG configurado fuera de tests → hecho de configuración
        if not is_test:
            for lineno, line in enumerate(lines, 1):
                if _LEVEL_DEBUG_RE.search(line):
                    hallazgos.append(make_finding(
                        detector=DETECTOR, obligacion_id="gdpr-art-5",
                        archivo=rel, linea=lineno,
                        evidencia=line.strip()[:150],
                        tipo="DETERMINISTA",
                        mensaje=(
                            f"se detectó configuración de logging en nivel DEBUG/TRACE "
                            f"en {rel}:{lineno}; el repositorio no garantiza su desactivación "
                            "en producción (hecho de configuración)"
                        ),
                        prioridad_revision="MEDIA", confianza="alta",
                        obligaciones=obligaciones,
                    ))

    return hallazgos


def main(argv: list[str]) -> int:
    return run_detector_cli(sys.modules[__name__], argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
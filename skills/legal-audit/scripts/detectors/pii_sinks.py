#!/usr/bin/env python3
"""D1 — pii_sinks.py · DETERMINISTA → Art. 30(1)(d) · Art. 44-46

Flujo de datos de identificadores personales hacia salidas externas.

Inventaria campos de datos personales en modelos/esquemas/migraciones
(email, teléfono, dirección, nombre, nacimiento, documento, IP, device_id,
cookies, geolocalización y —crítico para STT— voz/audio/embedding/biometría)
y detecta sinks (HTTP a terceros, webhooks, email/SMS/push, logs, analytics,
object storage). Reporta el cruce campo → sink.

Regla de diseño: el detector NO decide si algo "cumple". Emite el hecho
observable "campo X (models.py:42) → POST https://api.third-party.com
(services/notify.py:88)". Para destinos externos se emite hallazgo bajo dos
obligaciones (hecho de inventario de destinatarios, Art. 30(1)(d) → 30; y
posible transferencia internacional, Arts. 44-46 → 44-49). El techo se
hereda del pack; jamás se sube.

Read-only sobre el repo auditado. Solo stdlib. Sin red.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    Finding,
    abs_to_rel,
    compile_alt,
    iter_source_files,
    load_obligaciones,
    make_finding,
    read_text,
    run_detector_cli,
)

DETECTOR = "pii_sinks"
COVERED_OBLIGACIONES = {"gdpr-art-30", "gdpr-art-44-49"}

# ---------------------------------------------------------------------------
# Inventario de campos de datos personales.
# (patrón, etiqueta, categoría, sensible)
PII_FIELD_PATTERNS = [
    (r"e-?mail|correo", "correo electrónico", "contacto", False),
    (r"phone|telefono|tel[eé]fono|celular|mobile|whatsapp|m(?:v)?phone", "teléfono", "contacto", False),
    (r"address|direccion|street|calle|postal|zip|city|ciudad|state|provincia", "dirección postal", "ubicación", False),
    (r"first_?name|last_?name|full_?name|nombre|apellido|surname", "nombre y apellido", "identidad", False),
    (r"birth(?:date|_date|day)?|fecha_?nacimiento|\bdob\b", "fecha de nacimiento", "identidad", False),
    (r"national_?id|passport|documento|identity_card|identificacion|\bdni\b|\brut\b|cedula|c[eé]dula|id_?number|cuit|cuil|tax_?id|ssn", "documento de identidad", "identidad", False),
    (r"ip_?address|remote_?addr|client_?ip|source_?ip|ipv4|ipv6|\bip\b", "dirección IP", "red", False),
    (r"device_?id|deviceid|user_?agent|\bua\b|ad_?id|idfa|imei", "identificador de dispositivo", "red", False),
    (r"cookie_?id|session_?id|fingerprint|visitor_?id|client_?id|advertising_?id", "cookie/identificador en línea", "red", False),
    (r"location|geo(?:_?location)?|latitude|longitude|\blat\b|\blon\b|gps|coords|posicion", "geolocalización", "ubicación", False),
    (r"voice|audio|speech|transcript|grabacion|grabaci[oó]n|llamada|call_?recording|waveform|utterance|acoustic", "voz/audio", "biométrico", True),
    (r"embedding|voice_?embedding|audio_?embedding|vector\b", "embedding de voz", "biométrico", True),
    (r"biometric|biometr[íi]a|face_?id|facial|iris|huella|fingerprint_?data|voiceprint", "dato biométrico", "biométrico", True),
]
PII_FIELD_RE = compile_alt([p for p, *_ in PII_FIELD_PATTERNS])

# Posición de declaración: nombre (con/sin comillas) seguido de `=` o `:`.
# Cubre `email = models.EmailField`, `email: str`, `"email": {...}`,
# `CREATE TABLE ... email VARCHAR`, `email VARCHAR(255)`.
#
# ALTA-2: antiguo `(?:^|[\"'(\[{,:= ])\s*` + nombre + `\s*` causaba
# backtracking polinomial sobre líneas largas de espacios (el `\s*` cedía un
# espacio a la vez para descubrir que no había nombre). Ahora el cuantificador
# es POSESSIVE (`\s*+`): si el nombre no sigue, la rama falla en O(1) sin
# rever; y la clase líder se prueba por posición (lineal).
_DECL_RE = re.compile(
    r"(?:^|[\"'(\[{,:= \t])"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*+"
    r"(?:[\"'])?\s*+(?P<post>[=:])",
)

# ---------------------------------------------------------------------------
# Sinks → (regex, categoría, destino por defecto)
SINK_PATTERNS = [
    (r"requests\.(?:get|post|put|patch|delete|options|request)\s*\(", "http_client", "externo"),
    (r"httpx\.(?:get|post|put|patch|delete|stream)\s*\(", "http_client", "externo"),
    (r"aiohttp\.(?:ClientSession|request)\s*\(", "http_client", "externo"),
    (r"urllib\.request\.urlopen\s*\(", "http_client", "externo"),
    (r"\bfetch\s*\(|XMLHttpRequest|axios\.(?:get|post|put|delete|patch|request)\s*\(|\.post\s*\(|\.put\s*\(", "http_sdk", "externo"),
    (r"\baxios\b|got\.|superagent\.|needle\.", "http_sdk", "externo"),
    (r"http\.(?:get|post|put|delete|request)\s*\(", "http_sdk", "externo"),
    (r"smtplib|sendgrid|ses\.sendEmail|nodemailer|mailgun|mandrill|mailchimp|sendmail|send_?mail|mail\(\)|mailer\.", "email", "externo"),
    (r"twilio|fcm|firebase_messaging|messaging\(\)\.send|apns|onesignal|send_?push|push_?notification|send_?sms|sendSms|sms_?gateway", "sms_push", "externo"),
    (r"analytics\.|mixpanel|amplitude|segment\.|gtag\(|posthog|track_?event|trackEvent|heap\.|fullstory|clarity", "analytics", "externo"),
    (r"webhook|call_?webhook|dispatch_?event|(?<!def\s)notify\s*\(", "webhook", "externo"),
    (r"put_?object|upload_?file|upload_?blob|boto3|blob\.|storage\.bucket|firebase_storage|upload_?from|azure\.storage|presigned|signed_?url|object_?storage|\bs3\.", "object_storage", "externo"),
    (r"logger\.|logging\.|console\.log|print\s*\(|log\.(?:debug|info|warning|error|critical)|stdout|stderr|\.write\s*\(", "log", "interno"),
]
SINK_RES = [(compile_alt([p]), cat, default) for p, cat, default in SINK_PATTERNS]

# Hosts que no califican como destinatario externo.
_LOCAL_HOST_RE = re.compile(
    r"(?:localhost|127\.0\.0\.1|0\.0\.0\.0|::1|\.local|\.internal|\.test|"
    r"\.lan|\.localdomain|example\.com)$",
    re.IGNORECASE,
)
_URL_RE = re.compile(r"https?://([A-Za-z0-9._\-]+)", re.IGNORECASE)
_ENV_VAR_RE = re.compile(r"\b([A-Z][A-Z0-9_]{2,})\b")

# Objetos dúctiles: si un sink serializa alguno, puede arrastrar PII.
_DUMP_OBJ_RE = re.compile(
    r"\b(user|person|profile|record|customer|patient|client|contact|subscriber|"
    r"account|order|payload|body|data|item|self)\b",
    re.IGNORECASE,
)
_DUMP_CALL_RE = re.compile(
    r"(?:json\.dumps|JSON\.stringify|str\(|repr\(|pickle\.dumps|\bclone\b|\bcopy\b)"
    r"\s*\(\s*\w+\s*\)",
)


# ---------------------------------------------------------------------------
# config: resolución de variables de entorno / config para clasificar host.
def _config_url_map(root: Path) -> dict[str, str]:
    """Mapea `NOMBRE` → URL literal encontrada en configs/.env del repo."""
    out: dict[str, str] = {}
    for p in iter_source_files(root):
        text = read_text(p)
        for m in _ENV_VAR_RE.finditer(text):
            name = m.group(1)
            if name in out:
                continue
            line = text[max(0, text.rfind("\n", 0, m.start())):m.end() + 160]
            um = _URL_RE.search(line)
            if um:
                out[name] = um.group(0)
    return out


def _host_externo(url: str) -> bool:
    m = re.match(r"https?://([^/:\s]+)", url)
    if not m:
        return True
    return not bool(_LOCAL_HOST_RE.search(m.group(1)))


def _is_url_localhost(url: str) -> bool:
    m = re.match(r"https?://([^/:\s]+)", url)
    if not m:
        return False
    return bool(_LOCAL_HOST_RE.search(m.group(1)))


# ---------------------------------------------------------------------------
def scan(root: Path) -> list[Finding]:
    root = Path(root)
    obligaciones = load_obligaciones()
    hallazgos: list[Finding] = []

    # Config previa para clasificar URLs construidas con variables.
    url_map = _config_url_map(root)

    # --- (1) inventario de campos PII --------------------------------------
    # {(archivo, linea): (nombre, etiqueta, categoría, sensible)}
    campos: list[tuple[str, int, str, str, str, bool]] = []
    # primera declaración por nombre de campo (para citar el modelo real)
    campos_por_nombre: dict[str, tuple[str, int]] = {}

    for p in iter_source_files(root):
        rel = abs_to_rel(root, p)
        for lineno, line in enumerate(read_text(p).splitlines(), 1):
            for m in _DECL_RE.finditer(line):
                name = m.group("name")
                post = m.group("post")
                if (post != "=" and post != ":") or len(name) < 2:
                    continue
                fm = PII_FIELD_RE.search(name)
                if not fm:
                    continue
                # evita confundir imports/llamadas con declaraciones de campo:
                # `print(email)` no es declaración (post = '(' → ya filtrado).
                for pat, label, categoria, sensible in PII_FIELD_PATTERNS:
                    if re.search(fr"(?:^|_){pat}(?:$|_)", name, re.IGNORECASE) or re.fullmatch(pat, name, re.IGNORECASE):
                        campos.append((rel, lineno, name, label, categoria, sensible))
                        if name not in campos_por_nombre:
                            campos_por_nombre[name] = (rel, lineno)
                        break

    if not campos:
        return hallazgos

    # --- (2) sinks ---------------------------------------------------------
    sinks: list[dict] = []
    for p in iter_source_files(root):
        rel = abs_to_rel(root, p)
        for lineno, line in enumerate(read_text(p).splitlines(), 1):
            for sink_re, categoria, default in SINK_RES:
                if not sink_re.search(line):
                    continue
                # clasificación de destino
                urls = _URL_RE.findall(line)
                if urls:
                    ext_urls = [u for u in urls if _host_externo(u)]
                    local = any(_is_url_localhost(u) for u in urls)
                    destino = "externo" if ext_urls else ("interno" if local else "externo")
                    confianza = "alta"
                elif default == "externo":
                    # URL construida con variable o SDK cloud sin URL literal
                    vars_txt = [v for v in _ENV_VAR_RE.findall(line) if v in url_map]
                    resolved = [url_map[v] for v in vars_txt]
                    if any(_host_externo(u) for u in resolved):
                        destino, confianza = "externo", "alta"
                    elif resolved and all(not _host_externo(u) for u in resolved):
                        destino, confianza = "interno", "alta"
                    else:
                        destino, confianza = "posible_externo", "baja"
                else:
                    destino, confianza = default, "alta"
                sinks.append({
                    "archivo": rel, "linea": lineno, "categoria": categoria,
                    "destino": destino, "confianza": confianza,
                    "linea_txt": line.strip(),
                })
                break  # primera categoría que matchea la línea

    # --- (3) cruce campo → sink --------------------------------------------
    # Para cada sink, campos del mismo archivo en una ventana de ±4 líneas que
    # se refieran a él (nombre literal en la ventana) → cruce determinista.
    # `campos_por_archivo` ordenados por línea.
    by_file: dict[str, list[tuple[int, str, str, str, bool]]] = {}
    for rel, ln, name, label, cat, sens in campos:
        by_file.setdefault(rel, []).append((ln, name, label, cat, sens))

    def _window_hits(archivo: str, lineno: int) -> list[tuple[int, str, str, str, bool]]:
        lista = by_file.get(archivo, [])
        return [
            c for c in lista
            if c[0] <= lineno and abs(c[0] - lineno) <= 4
        ]

    for s in sinks:
        ventana_inicio = max(1, s["linea"] - 4)
        ventana_txt = ""
        for p in iter_source_files(root):
            if abs_to_rel(root, p) != s["archivo"]:
                continue
            lines = read_text(p).splitlines()
            ventana_txt = "\n".join(lines[ventana_inicio - 1:s["linea"] + 4])
            break

        directo = _window_hits(s["archivo"], s["linea"])
        # cruce directo: el nombre del campo (o su comilla) aparece en ventana
        cruzados: list[tuple[str, str, str, bool]] = []
        for ln, name, label, cat, sens in directo:
            if re.search(rf"[\"']?{re.escape(name)}[\"']?", ventana_txt, re.IGNORECASE) or \
               re.search(rf"\b{re.escape(name)}\b", ventana_txt, re.IGNORECASE):
                cruzados.append((name, label, cat, sens))

        # cruce suelto: se serializa un objeto que probablemente contiene PII
        dump_match = _DUMP_CALL_RE.search(ventana_txt) or _DUMP_OBJ_RE.search(ventana_txt)

        for name, label, cat, sens in cruzados:
            # donde se declara el campo (modelo real) para el cruce
            decl_rel, decl_ln = campos_por_nombre.get(name, (s["archivo"], ln))
            for obligacion_id in sorted(COVERED_OBLIGACIONES):
                if obligacion_id == "gdpr-art-44-49" and s["destino"] in ("interno", None):
                    continue  # solo transferencias van a 44-49
                prio = "ALTA" if sens or s["destino"] in ("externo", "posible_externo") else "MEDIA"
                mensaje = (
                    f"se detectó el campo {label} `{name}` ({decl_rel}:{decl_ln}) "
                    f"fluyendo a un sink {s['categoria']} con destino "
                    f"{s['destino']} ({s['archivo']}:{s['linea']})"
                )
                hallazgos.append(make_finding(
                    detector=DETECTOR, obligacion_id=obligacion_id,
                    archivo=s["archivo"], linea=s["linea"],
                    evidencia=f"campo `{name}` ({decl_rel}:{decl_ln}) → {s['linea_txt'][:140]}",
                    tipo="DETERMINISTA", mensaje=mensaje,
                    prioridad_revision=prio, confianza=s["confianza"],
                    destino=s["destino"], obligaciones=obligaciones,
                ))
        if not cruzados and dump_match and s["destino"] in ("externo", "posible_externo"):
            hit = [c for c in [_DUMP_OBJ_RE.search(ventana_txt)] if c]
            obj = hit[0].group(1).lower() if hit else "objeto"
            for obligacion_id in sorted(COVERED_OBLIGACIONES):
                prio = "ALTA" if s["destino"] == "externo" else "MEDIA"
                mensaje = (
                    f"se detectó serialización del objeto `{obj}` ({s['archivo']}:{s['linea']}) "
                    f"hacia un sink {s['categoria']} con destino {s['destino']}; "
                    "el objeto puede contener campos de datos personales declarados en el repo"
                )
                hallazgos.append(make_finding(
                    detector=DETECTOR, obligacion_id=obligacion_id,
                    archivo=s["archivo"], linea=s["linea"],
                    evidencia=f"objeto `{obj}` serializado → {s['linea_txt'][:140]}",
                    tipo="DETERMINISTA", mensaje=mensaje,
                    prioridad_revision=prio, confianza="baja",
                    destino=s["destino"], obligaciones=obligaciones,
                ))

    return hallazgos


def main(argv: list[str]) -> int:
    return run_detector_cli(sys.modules[__name__], argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
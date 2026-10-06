#!/usr/bin/env python3
"""D5 — security_config.py · SEMI → Art. 32(1) + Art. 25(2)

Configuración de seguridad observable: verificación TLS deshabilitada,
CORS permisivo, ausencia de cabeceras de seguridad, ausencia de cifrado para
campos sensibles.

Techo SEMI — nunca SATISFIED: la AUSENCIA de cifrado/TLS/cabeceras es un
hecho; la ADECUACIÓN del cifrado al riesgo es juicio (Art. 32(2)). El
detector emite el hecho, nunca el juicio. Los hallazgos de configuración por
defecto (cabeceras, defaults) se mapean a Art. 25(2); los de verificación de
TLS/CORS/cifrado a Art. 32(1). Read-only. Solo stdlib. Sin red.
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

DETECTOR = "security_config"
COVERED_OBLIGACIONES = {"gdpr-art-32", "gdpr-art-25"}

_VERIFY_INSECURE_RE = compile_alt([
    r"verify\s*=\s*False", r"verify:\s*false", r"rejectUnauthorized\s*:\s*false",
    r"rejectUnauthorized\s*=\s*false", r"InsecureSkipVerify\s*:\s*true",
    r"InsecureSkipVerify\s*=\s*true", r"ssl_verify\s*=\s*False",
    r"check_hostname\s*=\s*False", r"allow_self_?signed\s*=\s*True",
    r"CURLOPT_SSL_VERIFYPEER.*?0", r"VERIFY_SSL\s*[=:]\s*False", r"TLS_REQUIRE\s*[=:]\s*False",
    r"no_?verify\s*[=:]\s*true", r"skip_?tls\s*[=:]\s*true", r"security\.ssl\s*[=:]\s*false",
])

# B3: la key con comilla de cierre (`"Access-Control-Allow-Origin": "*"`) requiere
# `\s*(?:["'])?\s*[=:]` entre key y separador; antes el patrón no matcheaba y el
# hallazgo de CORS no se emitía.
_CORS_ALLOW_ALL_RE = re.compile(r"Access-Control-Allow-Origin\s*(?:[\"'])?\s*[=:]\s*(?:[\"'])?\s*\*", re.IGNORECASE)
_CORS_CREDS_RE = re.compile(r"Access-Control-Allow-Credentials\s*(?:[\"'])?\s*[=:]\s*(?:true|[\"']?true)", re.IGNORECASE)

_TLS_ABSENT_RE = compile_alt([
    r"scheme\s*[=:]\s*[\"']?http[\"']?[^s]", r"protocol\s*[=:]\s*[\"']?http[\"']?[^s]",
    r"ws://", r"SECURE_SSL_REDIRECT\s*=\s*False", r"listen\s+80\s*;",
    r"force_ssl\s*[=:]\s*false", r"ssl_required\s*[=:]\s*false",
    r"server\s*[=:]\s*[\"']http",
])

# Cabeceras de seguridad buscadas en candidatos de configuración HTTP.
_SEC_HEADERS = [
    "Strict-Transport-Security", "Content-Security-Policy", "Content-Security",
    "X-Content-Type-Options", "X-Frame-Options",
]
_HTTP_ENTRY_RE = compile_alt([
    r"middleware", r"helmet", r"setHeader", r"add_header", r"headers\s*[=:]\s*\{",
    r"HTTP_PROXY|reverse.?proxy|CSP_|SECURE_", r"app\.use\s*\(", r"server\.use\s*\(",
])

# Campos sensibles y evidencia de cifrado en el repo.
_SENSITIVE_FIELD_RE = compile_alt([
    r"password|passwd|passphrase|contrase[ñn]a|\bclave\b", r"secret", r"ssn|cuit|cuil|rut\b",
    r"cvv|cvc|pan\b|card_?number|iban", r"api_?key|access_?key|private_?key|token",
    r"voice|audio|biometric|biometr[íi]a|embedding|fingerprint", r"national_?id|documento|dni\b|passport",
])
_CRYPTO_PRESENT_RE = compile_alt([
    r"encrypt|decrypt|cipher|aes|fernet|cryptography|sealed|kms|vault|hashlib",
    r"pbkdf|argon|bcrypt|scrypt|crypto-?js|forge\b|tink|openssl|libsodium|nacl|locksmith",
    r"gpg\b|age\b|sops\b", r"sha256|sha512|hmac",
])

_HEADER_SET_RE = re.compile("|".join(re.escape(h) for h in _SEC_HEADERS), re.IGNORECASE)


def _http_url_lines(root: Path) -> list[tuple[str, int, str]]:
    out = []
    for p in iter_source_files(root):
        rel = abs_to_rel(root, p)
        for lineno, line in enumerate(read_text(p).splitlines(), 1):
            if re.search(r"http://", line, re.IGNORECASE):
                m = re.search(r"(http://[^\s\"')\]]+)", line, re.IGNORECASE)
                if m and not re.match(r"http://(localhost|127\.0\.0\.1|0\.0\.0\.0|\.local|\.test|\.example)", m.group(1), re.IGNORECASE):
                    out.append((rel, lineno, m.group(1)))
    return out


def scan(root: Path) -> list[Finding]:
    root = Path(root)
    obligaciones = load_obligaciones()
    hallazgos: list[Finding] = []

    sent: set[tuple[str, str, int]] = set()

    def add(ob, archivo, linea, evidencia, mensaje, sev="MEDIA", conf="alta"):
        key = (ob, archivo, linea)
        if key in sent:
            return
        sent.add(key)
        hallazgos.append(make_finding(
            detector=DETECTOR, obligacion_id=ob,
            archivo=archivo, linea=linea,
            evidencia=evidencia[:200],
            tipo="SEMI", mensaje=mensaje,
            prioridad_revision=sev, confianza=conf,
            obligaciones=obligaciones,
        ))

    files = iter_source_files(root)
    # --- (1) verificación TLS deshabilitada (Art. 32(1)) -----------------
    for p in files:
        rel = abs_to_rel(root, p)
        for lineno, line in enumerate(read_text(p).splitlines(), 1):
            m = _VERIFY_INSECURE_RE.search(line)
            if m:
                add(
                    "gdpr-art-32", rel, lineno, line.strip(),
                    f"se detectó desactivación de verificación TLS/certificado (`{m.group(0)}`) "
                    f"en {rel}:{lineno}; sin esa verificación no se garantiza el canal cifrado hacia el destino",
                    sev="ALTA",
                )

    # --- (2) CORS permisivo con credenciales (Art. 32(1)) -----------------
    cors_all: list[tuple[str, int, str]] = []
    creds: set[str] = set()
    for p in files:
        rel = abs_to_rel(root, p)
        for lineno, line in enumerate(read_text(p).splitlines(), 1):
            if _CORS_ALLOW_ALL_RE.search(line):
                cors_all.append((rel, lineno, line.strip()[:150]))
            if _CORS_CREDS_RE.search(line):
                creds.add(rel)
    for rel, ln, ev in cors_all:
        if rel in creds:
            add(
                "gdpr-art-32", rel, ln, ev,
                f"se detectó CORS con origen `*` combinado con envío de credenciales en {rel}:{ln}; "
                "esa combinación permitiría a cualquier origen leer respuestas autenticadas",
                sev="ALTA",
            )

    # --- (3) protocolo sin TLS (Art. 32(1)) -------------------------------
    for rel, ln, url in _http_url_lines(root):
        add(
            "gdpr-art-32", rel, ln, url,
            f"se detectó URL de servicio en {url} (no TLS) en {rel}:{ln}; "
            "sin cifrado en tránsito no se garantiza la confidencialidad de lo transmitido",
            sev="MEDIA", conf="baja",
        )
    for p in files:
        rel = abs_to_rel(root, p)
        for lineno, line in enumerate(read_text(p).splitlines(), 1):
            m = _TLS_ABSENT_RE.search(line)
            if m:
                add(
                    "gdpr-art-32", rel, lineno, line.strip(),
                    f"se detectó configuración que no exige TLS (`{m.group(0)}`) en {rel}:{lineno}",
                    sev="MEDIA", conf="baja",
                )

    # --- (4) cabeceras de seguridad ausentes (Art. 25(2)) ------------------
    for p in files:
        rel = abs_to_rel(root, p)
        text = read_text(p)
        if not _HTTP_ENTRY_RE.search(text):
            continue
        present = {h for h in _SEC_HEADERS if re.search(h, text, re.IGNORECASE)}
        absent = [h for h in _SEC_HEADERS if h not in present]
        if absent:
            for ln, line in _first_http_entry(p, text):
                add(
                    "gdpr-art-25", rel, ln, line,
                    f"no se ha encontrado la cabecera de seguridad `{h}` en el candidato de "
                    f"entrada HTTP {rel}:{ln} (ausentes: {', '.join(absent)}); "
                    "hecho de configuración por defecto — la adecuación es juicio (Art. 25(2))",
                    sev="MEDIA", conf="baja",
                )
                break

    # --- (5) cifrado ausente para campos sensibles (Art. 32(1)) ------------
    sensibles: list[tuple[str, int, str]] = []
    crypto_hits: list[tuple[str, int, str]] = []
    for p in files:
        rel = abs_to_rel(root, p)
        for lineno, line in enumerate(read_text(p).splitlines(), 1):
            if _SENSITIVE_FIELD_RE.search(line):
                sensibles.append((rel, lineno, line.strip()[:150]))
            if _CRYPTO_PRESENT_RE.search(line):
                crypto_hits.append((rel, lineno, line.strip()[:150]))
    if sensibles:
        if crypto_hits:
            rel, ln, ev = crypto_hits[0]
            add(
                "gdpr-art-32", rel, ln, ev,
                f"se encontró uso de cifrado / función de hash en {rel}:{ln}; "
                "la adecuación del cifrado al riesgo queda como juicio (Art. 32(2))",
                sev="BAJA", conf="alta",
            )
        else:
            rel, ln, ev = sensibles[0]
            add(
                "gdpr-art-32", rel, ln, ev,
                f"se detectaron campos sensibles (p. ej. `{ev[:60]}`) en {rel}:{ln} y no se "
                "ha encontrado ninguna referencia a cifrado/hashing en el repositorio; "
                "hecho de ausencia — la adecuación es juicio (Art. 32(2))",
                sev="ALTA", conf="baja",
            )

    return hallazgos


def _first_http_entry(p: Path, text: str) -> list[tuple[int, str]]:
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if _HTTP_ENTRY_RE.search(line):
            hits.append((lineno, line.strip()[:100]))
    if hits:
        return hits[:1]
    return [(1, "(cabecera de entrada no identificada)")]


def main(argv: list[str]) -> int:
    return run_detector_cli(sys.modules[__name__], argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
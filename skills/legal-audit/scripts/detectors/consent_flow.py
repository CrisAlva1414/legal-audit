#!/usr/bin/env python3
"""D2 — consent_flow.py · DETERMINISTA → ePrivacy Art. 5(3) + Art. 7(3)

Orden de consentimiento respecto de cookies/fingerprinting/SDKs de terceros,
banners de cookies y casillas de consentimiento.

Regla crítica (ver epolicy sources + doctrine): una anomalía de cookies es
hallazgo de **ePrivacy Art. 5(3)** — NUNCA de Art. 6 GDPR. Ambos regímenes
son acumulativos e independientes (GDPR Art. 95, lex specialis). Las casillas
premarcadas en formularios de consentimiento sí se mapean a condiciones del
consentimiento GDPR Art. 7 (acción afirmativa, 4(11) / 7(2)).

Hechos emitidos (nunca juicios):
    - script de terceros / escritura de cookie/localStorage ANTES de la primera
      mención de un mecanismo de consentimiento en el mismo archivo;
    - banner de cookies sin camino de rechazo (solo "Aceptar");
    - checkbox de consentimiento premarcado;
    - ausencia de mecanismo de consentimiento cuando hay scripts de terceros.

Read-only. Solo stdlib. Sin red.
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

DETECTOR = "consent_flow"
COVERED_OBLIGACIONES = {"eprivacy-art-5-3", "gdpr-art-7"}

HTML_EXT = {".html", ".htm", ".js", ".ts", ".jsx", ".tsx", ".vue", ".svelte", ".py", ".go", ".rb", ".php", ".cs"}

# --- consentimiento: mecanismo / banners -----------------------------------
_CONSENT_RE = compile_alt([
    r"consent", r"cookie-?consent", r"didomi", r"onetrust", r"cookiebot",
    r"osano", r"tarteaucitron", r"cookiefirst", r"cmp[\"']?\s*[=:]",
    r"cookie.?banner", r"accept", r"aceptar", r"reject", r"rechazar",
    r"preferences", r"configurar", r"gdpr", r"lgpd", r"privacy",
])
_ACCEPT_RE = compile_alt([r"aceptar", r"accept|agree\b", r"\bok\b"])
_REJECT_RE = compile_alt([r"rechazar", r"reject|decline|deny\b", r"preferences", r"configurar", r"manage", r"decide"])

# --- banners reales (MEDIA: se acabaron los falsos "banner sin rechazo") ----
# Un banner es un ELEMENTO con id/class de banner/cookies/consentimiento, no
# cualquier línea con "accept". Un `Accept:` de header HTTP no es un banner.
_BANNER_MARKER_RE = compile_alt([
    r"id\s*=\s*[\"'][^\"']*(?:cookie|consent|gdpr|banner|modal|preferencias|preferences)[^\"']*[\"']",
    r"class\s*=\s*[\"'][^\"']*(?:cookie|consent|gdpr|banner|modal|preferencias|preferences)[^\"']*[\"']",
])
_BANNER_TEXT_RE = compile_alt([
    r"cookie-?banner", r"consent-?banner", r"gdpr-?banner",
    r"banner\s*(?:de\s*)?(?:cookies|consentimiento|privacidad)",
])
_HTTP_HEADER_LINE_RE = re.compile(r"^\s*Accept\s*:", re.IGNORECASE)

# --- scripts de terceros y escrituras en dispositivo ------------------------
_THIRDPARTY_SNIPPET_RE = compile_alt([
    r"fbq\s*\(", r"gtag\s*\(", r"googletagmanager", r"hotjar", r"clarity",
    r"crisp\.chat", r"intercom", r"segment\.", r"mixpanel", r"amplitude",
    r"fullstory", r"heap\.", r"branch\.", r"appsflyer", r"adjust\.", r"stripe\.js",
])
_EXTERNAL_SCRIPT_RE = re.compile(r"<script[^>]*\bsrc\s*=\s*[\"'](https?://[^\"']+)", re.IGNORECASE)
_COOKIE_WRITE_RE = compile_alt([
    r"document\.cookie\s*[+]=?\s*=", r"document\.cookie\s*=\s*[\"']",
    r"localStorage\.setItem", r"sessionStorage\.setItem",
])
_PRETICK_RE = compile_alt([
    r"<input[^>]*type\s*=\s*[\"']checkbox[\"'][^>]*checked",
    r"checked[^>]*type\s*=\s*[\"']checkbox[\"']",
    r"defaultChecked", r"defaultchecked",
])
_CONSENT_FIELD_RE = compile_alt([
    r"consent", r"marketing", r"news", r"promo", r"publicidad",
    r"boletin", r"newsletter", r"datos_personales", r"acepto",
])

_LOCAL_SCRIPT_HOST_RE = re.compile(r"(localhost|127\.0\.0\.1|0\.0\.0\.0|\.test|\.local)", re.IGNORECASE)


def _external_host(url: str) -> bool:
    m = re.match(r"https?://([^/:\s]+)", url)
    if not m:
        return True
    return not bool(_LOCAL_SCRIPT_HOST_RE.search(m.group(1)))


def _find_consent_line(lines: list[str]) -> int:
    """Primera línea (1-based) con mención de mecanismo de consentimiento."""
    for i, line in enumerate(lines, 1):
        if _CONSENT_RE.search(line):
            return i
    return 0


def scan(root: Path) -> list[Finding]:
    root = Path(root)
    obligaciones = load_obligaciones()
    hallazgos: list[Finding] = []

    for p in iter_source_files(root):
        if p.suffix.lower() not in HTML_EXT:
            continue
        rel = abs_to_rel(root, p)
        lines = read_text(p).splitlines()
        consent_line = _find_consent_line(lines)
        html = p.suffix.lower() in {".html", ".htm"}

        # (a) scripts de terceros antes del consentimiento ------------------
        for lineno, line in enumerate(lines, 1):
            for m in _EXTERNAL_SCRIPT_RE.finditer(line):
                url = m.group(1)
                if not _external_host(url):
                    continue
                if consent_line == 0 or lineno < consent_line:
                    hallazgos.append(make_finding(
                        detector=DETECTOR, obligacion_id="eprivacy-art-5-3",
                        archivo=rel, linea=lineno,
                        evidencia=line.strip()[:160],
                        tipo="DETERMINISTA",
                        mensaje=(
                            f"script de terceros `{url}` cargado en {rel}:{lineno}"
                            + (" antes de la primera mención de consentimiento del archivo "
                               f"({consent_line})" if consent_line else " sin mecanismo de consentimiento")
                            + "; hecho de ePrivacy Art. 5(3) (no de Art. 6 GDPR: regímenes acumulativos, GDPR Art. 95)"
                        ),
                        prioridad_revision="ALTA",
                        destino="externo", obligaciones=obligaciones,
                    ))
            for snippet in _THIRDPARTY_SNIPPET_RE.finditer(line):
                if consent_line == 0 or lineno < consent_line:
                    hallazgos.append(make_finding(
                        detector=DETECTOR, obligacion_id="eprivacy-art-5-3",
                        archivo=rel, linea=lineno,
                        evidencia=line.strip()[:160],
                        tipo="DETERMINISTA",
                        mensaje=(
                            f"SDK de terceros (plantilla tracker) `{snippet.group(0)}` "
                            f"en {rel}:{lineno}" +
                            (" antes de la primera mención de consentimiento del archivo"
                             if consent_line else " sin mecanismo de consentimiento en el archivo")
                        ),
                        prioridad_revision="ALTA",
                        destino="externo", obligaciones=obligaciones,
                    ))

        # (b) escritura de cookie/localStorage antes del consentimiento -----
        for lineno, line in enumerate(lines, 1):
            if not _COOKIE_WRITE_RE.search(line):
                continue
            if consent_line == 0 or lineno < consent_line:
                hallazgos.append(make_finding(
                    detector=DETECTOR, obligacion_id="eprivacy-art-5-3",
                    archivo=rel, linea=lineno,
                    evidencia=line.strip()[:160],
                    tipo="DETERMINISTA",
                    mensaje=(
                        f"escritura en dispositivo (`{_COOKIE_WRITE_RE.search(line).group(0)}`) "
                        f"en {rel}:{lineno}" +
                        (" antes de la primera mención de consentimiento del archivo"
                         if consent_line else " sin mecanismo de consentimiento en el archivo")
                    ),
                    prioridad_revision="ALTA",
                    destino="interno", obligaciones=obligaciones,
                ))

        # (c) banner sin camino de rechazo ----------------------------------
        # Solo cuentan banners REALES: un elemento con id/class de banner y
        # botones dentro del mismo bloque (±15 líneas). Express: 244 falsos
        # porque cualquier "accept"/"ok/.../manage" en ±10 líneas disparaba;
        # también matcheaba el header HTTP `Accept:`. Un marcador aislado SIN
        # botones baja la confianza a BAJA (hecho débil, no veredicto).
        banner_lines: list[int] = []
        for lineno, line in enumerate(lines, 1):
            if _BANNER_MARKER_RE.search(line) or _BANNER_TEXT_RE.search(line):
                banner_lines.append(lineno)
        banners_vistos: set[str] = set()  # dedupe por bloque de banner (B2)
        for bl in banner_lines:
            bloque = "\n".join(lines[max(0, bl - 15):bl + 16]).lower()
            if bloque in banners_vistos:
                continue
            banners_vistos.add(bloque)
            # headers HTTP: un bloque que es request header no es un banner
            if _HTTP_HEADER_LINE_RE.match(lines[bl - 1]):
                continue
            if re.search(r"(?m)^\s*Accept\s*:", bloque):
                continue
            has_accept = bool(_ACCEPT_RE.search(bloque))
            has_reject = bool(_REJECT_RE.search(bloque))
            if has_accept and not has_reject:
                hallazgos.append(make_finding(
                    detector=DETECTOR, obligacion_id="eprivacy-art-5-3",
                    archivo=rel, linea=bl,
                    evidencia=lines[bl - 1][:160] if bl - 1 < len(lines) else "",
                    tipo="DETERMINISTA",
                    mensaje=(
                        f"banner de cookies con aceptación pero sin camino de rechazo "
                        f"(no se observa 'Rechazar'/'Preferencias'/'Configurar' en el bloque "
                        f"en {rel}:{bl}); hecho de ePrivacy Art. 5(3)"
                    ),
                    prioridad_revision="MEDIA", confianza="alta",
                    destino="interno", obligaciones=obligaciones,
                ))
            elif not has_accept and not has_reject:
                # marcador de banner aislado, sin botones: presencia débil
                hallazgos.append(make_finding(
                    detector=DETECTOR, obligacion_id="eprivacy-art-5-3",
                    archivo=rel, linea=bl,
                    evidencia=lines[bl - 1][:160] if bl - 1 < len(lines) else "",
                    tipo="DETERMINISTA",
                    mensaje=(
                        f"se encontró un marcador de banner de cookies ({rel}:{bl}) sin "
                        "botones de aceptación/rechazo observables en el bloque; hecho de "
                        "presencia débil — el camino de consentimiento no es verificable aquí"
                    ),
                    prioridad_revision="BAJA", confianza="baja",
                    destino="interno", obligaciones=obligaciones,
                ))

        # (d) casillas premarcadas -----------------------------------------
        for lineno, line in enumerate(lines, 1):
            if not _PRETICK_RE.search(line):
                continue
            if not _CONSENT_FIELD_RE.search(line):
                continue
            hallazgos.append(make_finding(
                detector=DETECTOR, obligacion_id="gdpr-art-7",
                archivo=rel, linea=lineno,
                evidencia=line.strip()[:160],
                tipo="DETERMINISTA",
                mensaje=(
                    f"checkbox de consentimiento premarcado en {rel}:{lineno}: "
                    "se detecta `checked`/`defaultChecked` sobre un campo de consentimiento; "
                    "el consentimiento por acción afirmativa (GDPR Art. 4(11)/7(2)) no puede "
                    "inferirse de una casilla premarcada"
                ),
                prioridad_revision="MEDIA",
                destino="interno", obligaciones=obligaciones,
            ))

    return hallazgos


def main(argv: list[str]) -> int:
    return run_detector_cli(sys.modules[__name__], argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
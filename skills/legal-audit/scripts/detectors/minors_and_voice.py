#!/usr/bin/env python3
"""D6 — minors_and_voice.py · SEMI → Art. 8 / Art. 9(1) / Art. 16 quáter · cl-8° bis

Detector especializado en el caso de uso STT sobre voz: presencia de edad /
minoría, umbrales etarios, procesamiento de voz/audio/embedding (categoría
especial) y rutas de decisión automatizada sobre menores.

Regla de umbrales (implementada con cuidado):
  - Chile (Art. 16 quáter Ley 21.719) tiene TRES umbrales NNA: <14 parental
    para todo; 14-17 consentimiento propio; y <16 parental para DATOS
    SENSIBLES. La UE (Art. 8 GDPR) tiene UNO (16, o 13 si el Estado lo bajó).
  - Un único check `age >= 16` es INCORRECTO para Chile: no distingue el
    umbral de sensibles (<16) del general (<14).
  - Si el código usa un único umbral, se emite el hecho (no el juicio) de que
    la regla chilena requiere umbrales diferenciados y que el umbral de
    sensibles es <16, no <14.

Hechos emitidos (nunca juicios): umbral(es) observados, coexistencia de
voz+edad, falta de age-gate, falta de autorización parental, decisión
automatizada sobre datos de menores. Read-only. Solo stdlib. Sin red.
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

DETECTOR = "minors_and_voice"
COVERED_OBLIGACIONES = {"gdpr-art-8", "gdpr-art-9", "cl-16-quater", "cl-8-bis"}

# Campos de edad/menoría SOLO en contexto de identidad (acceso a campo o
# declaración), nunca una palabra en un párrafo: "regardless of age" no es un
# campo. Regla práctica: precedido por `.`/`_`-` o seguido de `)`/`=`/`,`/`:`
# (o `[`/`]` para `children[0]`). ALTA-3: elimina los falsos positivos de
# prosa en inglés y español.
_AGE_FIELD_TOKEN = (
    r"age|edad|birthdate|fecha_?nacimiento|date_of_birth|\bdob\b|is_?minor|"
    r"is_?child|age_?group|\bminor\b|\bmenor\b|children?|\bnna\b"
)
# Lineal: el separador se busca primero (falla O(1) en runs de letras) y el
# token+delimitador usa `\s*+` (possessive), sin backtracking polinomial.
_AGE_FIELD_RE = re.compile(
    r"(?:"
    r"[._-](?:" + _AGE_FIELD_TOKEN + r")"
    r"|(?:" + _AGE_FIELD_TOKEN + r")\s*+[)=,:;[\]]"
    r")",
    re.IGNORECASE,
)

_VOICE_RE = compile_alt([
    r"voice|audio|speech|speech-?to-?text|\bstt\b|transcript|grabaci[oó]n|llamada",
    r"utterance|waveform|acoustic|embedding|voice_?embedding|audio_?embedding|vector\b",
    r"biometric|biometr[íi]a|face_?id|facial|voiceprint|huella",
    r"\bwhisper\b|\bdeepspeech\b|\btranscri",
])

_PARENTAL_AUTH_RE = compile_alt([
    r"parental|parent_?consent|consent_?parental|guardian|tutor|apoderado",
    r"autoriza\w*(?:parental|padres|tutor|representante)", r"verif\w*(?:parental|tutor|edad)",
    r"age_?gate|edad_?minima|verify.?age|verific\w*edad",
])

_AUTODECISION_RE = compile_alt([
    r"\bscore\b|scoring|\brank(?:ing)?\b|clasif|\bclassifier\b|model\.predict|puntuacion",
    r"decision_?auto|auto_?decision|automat\w*(?:decision|decisi[oó]n)", r"machine.?learning",
    r"\bML\b|\bAI\b|inferencia|inference|perfil\w*(?:automatico|automático|conducta)",
])

# --- documentación: nunca se escanea para este detector (ALTA-3) -----------
# Un README.md/CODE_OF_CONDUCT.md/LICENCIA dice "age", "voice", "classify",
# "AI", etc. en prosa: matchear ahí es siempre falso positivo.
_DOC_EXCLUDED_EXTS = {".md", ".txt", ".rst"}
_DOC_EXCLUDED_PARTS = {"docs", "doc", "documentation"}
_DOC_EXCLUDED_STEMS = {"license", "changelog", "contributing", "code_of_conduct",
                       "code-of-conduct", "readme", "security", "authors"}


def _es_documentacion(rel: str, path: Path) -> bool:
    if path.suffix.lower() in _DOC_EXCLUDED_EXTS:
        return True
    if any(part.lower() in _DOC_EXCLUDED_PARTS for part in Path(rel).parts):
        return True
    stem = path.stem.lower().replace("-", "_").replace(" ", "_")
    return stem in _DOC_EXCLUDED_STEMS


# --- comparaciones de edad: parser manual lineal (ALTA-2) -------------------
# Antiguo `_AGE_CMP_RE` (regex con `[\w.]*\b(?:age|…)` y `\s*`) era
# polinomial sobre líneas largas de un mismo carácter. Reemplazado por un
# parser manual sin cuantificadores anidados.
_AGE_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*", re.IGNORECASE)
_NUM_RE = re.compile(r"\d{1,2}")
_CMP_OP_RE = re.compile(r"!==|===|>=|<=|==|!=|>|<")
_AGE_TAIL_RE = re.compile(
    r"(?:^|[._])(age|edad|minor|dob|birthdate|fecha_nacimiento|date_of_birth|"
    r"is_minor|is_child|age_group)$",
    re.IGNORECASE,
)


def _iter_age_cmps(line: str) -> list[tuple[str, int]]:
    """Comparaciones `(op, num)` de un campo de edad en `line`.

    Dos pasadas lineales (token-edad → op → número, y número → op →
    token-edad). Sin backtracking: cada token se consume una vez.
    """
    out: list[tuple[str, int]] = []
    # dirección: <campo> <op> <num>
    for m in _AGE_TOKEN_RE.finditer(line):
        if not _AGE_TAIL_RE.search(m.group(0)):
            continue
        j = m.end()
        while j < len(line) and line[j] in " \t":
            j += 1
        opm = _CMP_OP_RE.match(line, j)
        if not opm:
            continue
        j2 = opm.end()
        while j2 < len(line) and line[j2] in " \t":
            j2 += 1
        nm = _NUM_RE.match(line, j2)
        if nm:
            out.append((opm.group(0), int(nm.group(0))))
    # dirección: <num> <op> <campo>
    for m in _NUM_RE.finditer(line):
        j = m.end()
        while j < len(line) and line[j] in " \t":
            j += 1
        opm = _CMP_OP_RE.match(line, j)
        if not opm:
            continue
        j2 = opm.end()
        while j2 < len(line) and line[j2] in " \t":
            j2 += 1
        tm = _AGE_TOKEN_RE.match(line, j2)
        if tm and _AGE_TAIL_RE.search(tm.group(0)):
            out.append((opm.group(0), int(m.group(0))))
    return out

_CTX_CONSENT_RE = compile_alt([
    r"consent", r"parental", r"autoriz", r"permit", r"gate", r"minor", r"menor",
    r"children", r"child", r"kids", r"\bnna\b", r"edad", r"age\b", r"adult",
])
# números de umbral relevantes: 13 (UE mínimo), 14 (CL todo), 16 (CL sensibles / UE default), 18
_RELEVANT_NUMS = {13, 14, 15, 16, 17, 18}


def scan(root: Path) -> list[Finding]:
    root = Path(root)
    obligaciones = load_obligaciones()
    hallazgos: list[Finding] = []

    age_hits: list[tuple[str, int, str]] = []
    voice_hits: list[tuple[str, int, str]] = []
    parental_hits: list[tuple[str, int, str]] = []
    autodec_hits: list[tuple[str, int, str]] = []
    threshold_hits: list[tuple[str, int, int, str, str]] = []  # (file,line,num,op,snippet)

    for p in iter_source_files(root):
        rel = abs_to_rel(root, p)
        if _es_documentacion(rel, p):
            continue
        for lineno, line in enumerate(read_text(p).splitlines(), 1):
            if _AGE_FIELD_RE.search(line):
                age_hits.append((rel, lineno, line.strip()[:140]))
            if _VOICE_RE.search(line):
                voice_hits.append((rel, lineno, line.strip()[:140]))
            if _PARENTAL_AUTH_RE.search(line):
                parental_hits.append((rel, lineno, line.strip()[:140]))
            if _AUTODECISION_RE.search(line):
                autodec_hits.append((rel, lineno, line.strip()[:140]))
            for op, num in _iter_age_cmps(line):
                if num not in _RELEVANT_NUMS:
                    continue
                # contexto: la línea menciona consent/edad/menor
                if not _CTX_CONSENT_RE.search(line):
                    continue
                threshold_hits.append((rel, lineno, num, op, line.strip()[:140]))

    # --- (1) temperatura: no hay nada de menores ni voz → sin hallazgos ----
    if not age_hits and not voice_hits:
        return hallazgos

    # --- (2) umbrales etarios (cl-16-quater / Art. 8) -----------------------
    nums = sorted({n for _, _, n, _, _ in threshold_hits})
    voz_o_minor = bool(voice_hits and age_hits)
    # D13: una app restringida SOLO a adultos (`>=18`) es *más* restrictiva,
    # no menos; el bug de "umbral único" existe cuando el único umbral es
    # <14 o solo <16. Nunca se emite ALTA por un gate adulto.
    adult_gate = bool(threshold_hits) and all(
        (op in (">", ">=") and num >= 18)
        for _, _, num, op, _ in threshold_hits
    )

    if threshold_hits:
        if {14, 16}.issubset(set(nums)):
            # presencia: umbrales diferenciados 14/16
            rel, ln, _, _, snippet = threshold_hits[0]
            hallazgos.append(make_finding(
                detector=DETECTOR, obligacion_id="cl-16-quater",
                archivo=rel, linea=ln,
                evidencia=snippet,
                tipo="SEMI",
                mensaje=(
                    f"se encontraron umbrales etarios diferenciados 14/16 en {rel}:{ln} "
                    f"(valores observados: {nums}); hecho de presencia compatible con la "
                    "diferenciación chilena (Ley 21.719 Art. 16 quáter: <14 parental para todo; "
                    "<16 parental para sensibles)"
                ),
                prioridad_revision="BAJA", confianza="alta", obligaciones=obligaciones,
            ))
        else:
            rel, ln, num, op, snippet = threshold_hits[0]
            if adult_gate:
                hallazgos.append(make_finding(
                    detector=DETECTOR, obligacion_id="cl-16-quater",
                    archivo=rel, linea=ln,
                    evidencia=snippet,
                    tipo="SEMI",
                    mensaje=(
                        f"se detectó umbral etario único {op} {num} en {rel}:{ln} "
                        f"(valores observados: {nums}); restringir SOLO a adultos (>=18) excluye "
                        "a menores y es más restrictiva que los umbrales chilenos (<14/<16), "
                        "por lo que no sugiere riesgo de datos de menores; hecho de constancia"
                    ),
                    prioridad_revision="BAJA", confianza="alta", obligaciones=obligaciones,
                ))
            else:
                hallazgos.append(make_finding(
                    detector=DETECTOR, obligacion_id="cl-16-quater",
                    archivo=rel, linea=ln,
                    evidencia=snippet,
                    tipo="SEMI",
                    mensaje=(
                        f"se detectó umbral etario único {num} en {rel}:{ln} "
                        f"(valores observados: {nums}); la regla chilena (Art. 16 quáter) exige "
                        "umbrales diferenciados: <14 parental para todo, 14-17 consentimiento "
                        "propio, y <16 parental para datos sensibles — un único check es insuficiente "
                        "para Chile; para la UE el default es 16 (Art. 8, o 13 si el Estado lo bajó)"
                    ),
                    prioridad_revision="ALTA" if voz_o_minor else "MEDIA",
                    confianza="alta", obligaciones=obligaciones,
                ))
    elif voz_o_minor:
        rel, ln, _ = age_hits[0]
        hallazgos.append(make_finding(
            detector=DETECTOR, obligacion_id="cl-16-quater",
            archivo=rel, linea=ln,
            evidencia="",
            tipo="SEMI",
            mensaje=(
                f"se encontraron campos de edad/menoría ({rel}:{ln}) pero no se observó ningún "
                "umbral etario (14/16) ni referencia a autorización parental en el repositorio"
            ),
            prioridad_revision="ALTA", confianza="baja", obligaciones=obligaciones,
        ))

    # --- (3) voz + datos de menores: categoría especial sobre menores --------
    if voz_o_minor:
        rel, ln, _ = voice_hits[0]
        hallazgos.append(make_finding(
            detector=DETECTOR, obligacion_id="gdpr-art-9",
            archivo=rel, linea=ln,
            evidencia=voice_hits[0][2],
            tipo="SEMI",
            mensaje=(
                f"se detectó procesamiento de voz/audio/embedding en {rel}:{ln} coexistiendo con "
                "campos de edad/menoría en el repositorio; la voz que identifica unívocamente es "
                "categoría especial (Art. 9(1)) y sobre menores requiere base 9(2) explícita"
            ),
            prioridad_revision="ALTA", confianza="alta", obligaciones=obligaciones,
        ))
    elif voice_hits:
        rel, ln, _ = voice_hits[0]
        hallazgos.append(make_finding(
            detector=DETECTOR, obligacion_id="gdpr-art-9",
            archivo=rel, linea=ln,
            evidencia=voice_hits[0][2],
            tipo="SEMI",
            mensaje=(
                f"se detectó procesamiento de voz/audio/embedding en {rel}:{ln} "
                "(categoría especial del Art. 9(1) cuando identifica unívocamente a una persona)"
            ),
            prioridad_revision="MEDIA", confianza="media", obligaciones=obligaciones,
        ))

    # --- (4) falta de age-gate / autorización parental (Art. 8 GDPR) ---------
    if voz_o_minor and not parental_hits:
        rel, ln, _ = age_hits[0]
        hallazgos.append(make_finding(
            detector=DETECTOR, obligacion_id="gdpr-art-8",
            archivo=rel, linea=ln,
            evidencia=age_hits[0][2],
            tipo="SEMI",
            mensaje=(
                f"se encontraron datos de menores ({rel}:{ln}) y procesamiento de voz sin ninguna "
                "referencia a age-gate ni verificación de autorización parental en el repositorio"
                " (Art. 8 GDPR exige consentimiento/autorización parental bajo 16, salvo ley estatal)"
            ),
            prioridad_revision="ALTA", confianza="baja", obligaciones=obligaciones,
        ))

    # --- (5) decisión automatizada sobre menores (cl-8° bis) -----------------
    if autodec_hits and (age_hits or voice_hits):
        rel, ln, _ = autodec_hits[0]
        hallazgos.append(make_finding(
            detector=DETECTOR, obligacion_id="cl-8-bis",
            archivo=rel, linea=ln,
            evidencia=autodec_hits[0][2],
            tipo="SEMI",
            mensaje=(
                f"se detectaron rutas de puntuación/clasificación/decisión automatizada en "
                f"{rel}:{ln} coexistiendo con datos de menores o de voz; en Chile (Ley 21.719 "
                "Art. 8° bis) requieren canal de intervención humana, registro de la lógica y "
                "explicación entregada — se reporta la coexistencia, no su licitud"
            ),
            prioridad_revision="ALTA", confianza="baja", obligaciones=obligaciones,
        ))

    return hallazgos


def main(argv: list[str]) -> int:
    return run_detector_cli(sys.modules[__name__], argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
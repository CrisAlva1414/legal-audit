#!/usr/bin/env python3
"""Verificaciones de integridad y consistencia del pack de evidencia.

Siete checks (solo stdlib, sin red, deterministas):

  1. Anclas e indices: todo link interno `#ancla` (mismo archivo o cross-file)
     resuelve a un `<a id="...">` existente.
  2. Contaminacion: frases prohibidas por `doctrine.md` no aparecen como
     afirmaciones; cada coincidencia legítima debe estar en un bloque doctrinal
     o marcada con `❌`. El propio verificador se escanea a sí mismo; solo se
     omite el bloque explícito donde se declaran las constantes (ver
     `PROHIBITED_PHRASES`).
  3. Conteo de palabras por archivo.
  4. Crosswalk: la Tabla 1 tiene exactamente 13 filas, cada dimensión trae
     artículo en ambos lados, y todo artículo referido está en la allowlist
     del pack (GDPR / Ley 19.628 mod. 21.719).
  5. Campos por obligación: GDPR exige 4 campos (cita, operacionalización,
     determinismo, caveat) y Chile 5 (+ "diferencia con el GDPR"); la ausencia
     del quinto campo en GDPR debe estar declarada explícitamente. El
     determinismo declarado debe ser uno del enum y coherente con el nivel que
     la doctrina asigna a cada artículo (cierra T2→T5). Las citas no pueden
     ser vacías ni placeholder.
  6. Hash (SHA-256) del pack contra `sources/SOURCES.sha256` (mitiga T2).
     Falla si un archivo listado no existe, no coincide, o si hay archivos en
     `references/sources/` fuera del manifiesto.
  7. Obligations generadas (`references/obligations/obligations.json`):
     valida que cada ficha tenga determinismo del enum, techo_de_veredicto
     coherente con el determinismo (doctrine.md) y id único. Control nuclear:
     un determinismo `JUICIO` o `NO-VERIFICABLE-ESTATICAMENTE` nunca puede
     declarar `SATISFIED`. Si obligations.json no existe o tiene menos de 30
     fichas, falla (no pass silencioso).

Uso:
    python3 verify_pack.py            # corre los 7 checks
    python3 verify_pack.py 1 4        # corre solo los checks indicados
Exit code 0 si todos los checks corren sin fallos; 1 si alguno falla.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

# --- rutas -----------------------------------------------------------------
# <root>/skills/legal-audit/scripts/verify_pack.py
SCRIPT = Path(__file__).resolve()
SKILL_DIR = SCRIPT.parents[1]           # skills/legal-audit
REFERENCES = SKILL_DIR / "references"   # skills/legal-audit/references
SOURCES = REFERENCES / "sources"
ROOT = SCRIPT.parents[3]                # raiz del repo

# Directorios que nunca son parte del pack ni del código auditado.
# `tests/` contiene las frases prohibidas como *inputs* de los tests de
# evasión; no se escanea para contaminación porque no es contenido de la
# skill (no se carga en runtime, no se emite en reportes). El resto ya estaba
# en la lista. El script de verificación ya no se autoexcluye: solo omite el
# bloque marcado de sus propias constantes (ver check_contamination).
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "tests"}
TEXT_EXT = {".md", ".py", ".txt", ".json", ".yml", ".yaml", ".sh", ".js",
            ".ts", ".toml", ".cfg", ".ini", ".html"}

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
ANCHOR_RE = re.compile(r'<a\s+id=["\']([^"\']+)["\']\s*>')
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")

# --- normalización ---------------------------------------------------------
# Antes de evaluar contaminación y determinismo se normaliza el texto:
# minúsculas, sin acentos, sin puntuación, espacios colapsados. Los
# La negación se detecta porque el token de "≠" sobrevive a la normalización:
# una frase que niega la equiparación (desindexar "no es lo mismo que" borrar)
# no dispara el patrón prohibido, que exige el operador de afirmación.
_OPERATOR_TOKENS = {"≠": " neq ", "≥": " ge ", "≤": " le ", "=": " eq "}


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


def normalize(text: str) -> str:
    # Los operadores se convierten ANTES de quitar acentos: NFKD descompone
    # "≠" en "=" + overlay, y el overlay se descarta, colapsando la negación
    # en afirmación. Mapeándolos primero se conserva la distinción.
    t = text.lower()
    for op, tok in _OPERATOR_TOKENS.items():
        t = t.replace(op, tok)
    t = _strip_accents(t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


# --- frases prohibidas -----------------------------------------------------
# BEGIN PROHIBITED PHRASES — bloque que check_contamination omite por
# marcador EXPLÍCITO (no es self-exclusión del archivo; es el reconocimiento
# de las constantes declaradas como tales). Cada patrón está normalizado
# (minúsculas, sin tildes, espacios colapsados) y trazado a la línea de
# references/doctrine.md que lo origina.
PROHIBITED_PHRASES = [
    # doctrine.md:45 — "cumple con la ley" / "GDPR compliant"
    r"cumple con (?:la|las) ley(?:es)?|gdpr compliant",
    # doctrine.md:48 — "garantiza anonimización"
    r"garantiza (?:la )?anonimiza(?:cion|do)",
    # doctrine.md:50 — "cumple el Art. 32"
    r"cumple el art(?:iculo)? 32",
    # doctrine.md:52 — "cumple el plazo de 72 horas" (o "cumple con plazo …")
    r"cumple (?:el |con el |con )?plazo de 72 horas",
    # doctrine.md:54 — "la auditoría pasó"
    r"la auditoria paso",
    # doctrine.md:56 — "no encontré identificadores, es anónimo"
    r"no encontre identificadores.{0,20}anonimo",
    # doctrine.md:58 — "cumple con ISO 27701"
    r"cumple con iso 27701",
    # doctrine.md:60 — "k≥5, es anónimo"
    r"k ge 5.{0,12}anonimo",
    # doctrine.md:62 — "desindexar = borrar"
    r"desindexar (?:eq|es|igual a) borrar",
    # doctrine.md:64 — sobreafirmación simétrica (I5): "incumple la ley"
    r"incumple (?:la|las) ley(?:es)?",
    # doctrine.md:64 — "viola el Art. X"
    r"viola el art(?:iculo)? \d+",
    # doctrine.md:64 — "es ilegal"
    r"es ilegal",
]
# END PROHIBITED PHRASES

# Secciones que DOCUMENTAN las prohibiciones (la frase aparece como regla,
# no como afirmación). Es el contexto explícito que, junto con `❌`, hace
# legítima una mención.
DOCTYPE_SECTION_RE = re.compile(
    r"(qué nunca|nunca se afirma|no afirmar|trampas|errores de interpretación)",
    re.IGNORECASE,
)


class RootError(RuntimeError):
    """El directorio raíz no contiene la skill (instalación copiada)."""


def resolve_root(root: Path | None = None) -> Path:
    """Valida que la raíz contenga la skill; aborta si no (I4)."""
    r = Path(root).resolve() if root is not None else Path(ROOT).resolve()
    sentinel = r / "skills" / "legal-audit" / "SKILL.md"
    if not sentinel.is_file():
        raise RootError(
            f"ROOT inválido: {r} no contiene skills/legal-audit/SKILL.md. "
            "La skill parece instalada copiada (no por symlink al repo). "
            "Abortando: no se opera sobre un directorio que no sea el repo."
        )
    return r


def _paths(root: Path) -> tuple[Path, Path, Path]:
    skill = root / "skills" / "legal-audit"
    return skill, skill / "references", skill / "references" / "sources"


def repo_text_files(root: Path) -> list[Path]:
    out = []
    for p in root.rglob("*"):
        if p.is_dir() or p.suffix.lower() not in TEXT_EXT:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        out.append(p)
    return sorted(out)


def repo_md_files(root: Path) -> list[Path]:
    out = []
    for p in root.rglob("*"):
        if p.is_dir() or p.suffix.lower() != ".md":
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        out.append(p)
    return sorted(out)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# --- check 1: anclas --------------------------------------------------------
def check_anchors(root: Path | None = None) -> list[str]:
    root = resolve_root(root)
    failures: list[str] = []
    anchors: dict[Path, set[str]] = {}
    for md in repo_md_files(root):
        anchors[md.resolve()] = set(ANCHOR_RE.findall(read_text(md)))

    for md in repo_md_files(root):
        target_self = md.resolve()
        for lineno, line in enumerate(read_text(md).splitlines(), 1):
            for raw in LINK_RE.findall(line):
                url = raw.strip()
                if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url) or url.startswith("mailto:"):
                    continue
                if "#" not in url:
                    continue
                path_part, frag = url.split("#", 1)
                if not frag:
                    continue
                if path_part in ("", md.name):
                    target = target_self
                else:
                    target = (md.parent / path_part).resolve()
                    if not target.exists():
                        failures.append(
                            f"  ROTO {md.relative_to(root)}:{lineno}: "
                            f"archivo destino inexistente -> {url}"
                        )
                        continue
                if frag not in anchors.get(target, set()):
                    failures.append(
                        f"  ROTO {md.relative_to(root)}:{lineno}: "
                        f'ancla "#{frag}" sin <a id> en {target.relative_to(root)}'
                    )
    return failures


# --- check 2: contaminacion -------------------------------------------------
# Los marcadores se construyen dinámicamente para que la línea que los usa
# dentro de `_prohibited_block_lines` no contenga el literal (la búsqueda no
# debe matchearse a sí misma).
_PHRASE_MARK_BEG = "# BEGIN" + " PROHIBITED PHRASES"
_PHRASE_MARK_END = "# END" + " PROHIBITED PHRASES"


def _prohibited_block_lines(lines: list[str]) -> set[int]:
    """Líneas del bloque marcado con los comentarios centinela."""
    start = end = None
    for i, line in enumerate(lines):
        if _PHRASE_MARK_BEG in line:
            start = i
        if _PHRASE_MARK_END in line:
            end = i
    if start is None or end is None or end < start:
        return set()
    return set(range(start, end + 1))


def check_contamination(root: Path | None = None) -> tuple[list[str], list[str]]:
    root = resolve_root(root)
    legit: list[str] = []
    flags: list[str] = []
    seen: set[tuple[Path, int, str]] = set()

    def add(kind: str, path: Path, lineno: int, phrase: str, ctx: str) -> None:
        key = (path.resolve(), lineno, phrase)
        if key in seen:
            return
        seen.add(key)
        rec = f"  {path.relative_to(root)}:{lineno} [{phrase}] {ctx}"
        (legit if kind == "legit" else flags).append(rec)

    for path in repo_text_files(root):
        text = read_text(path)
        if "\x00" in text:
            continue
        lines = text.splitlines()
        skip = _prohibited_block_lines(lines)
        current_section = ""
        for i, line in enumerate(lines):
            if i in skip:
                continue
            heading = HEADING_RE.match(line)
            if heading:
                current_section = heading.group(2)
            # Ventana de hasta 2 líneas consecutivas (atrapa frases partidas).
            window_lines = [line]
            if i + 1 < len(lines) and (i + 1) not in skip:
                window_lines.append(lines[i + 1])
            window = " ".join(window_lines)
            norm = normalize(window)
            section_ok = bool(DOCTYPE_SECTION_RE.search(current_section))
            marked = "❌" in window
            for phrase in PROHIBITED_PHRASES:
                if not re.search(phrase, norm):
                    continue
                ctx = line.strip()
                if len(ctx) > 160:
                    ctx = ctx[:157] + "..."
                if marked or section_ok:
                    add("legit", path, i + 1, phrase, ctx)
                else:
                    add("flag", path, i + 1, phrase, ctx)
    return legit, flags


# --- check 3: conteo de palabras -------------------------------------------
def check_wordcount(root: Path | None = None) -> list[str]:
    root = resolve_root(root)
    rows = []
    total = 0
    for md in repo_md_files(root):
        words = len(read_text(md).split())
        total += words
        rows.append(f"  {words:>6}  {md.relative_to(root)}")
    rows.append(f"  {total:>6}  TOTAL")
    return rows


# --- check 4: crosswalk tabla 1 --------------------------------------------
def _table_rows(section_text: str) -> list[list[str]]:
    rows = []
    for line in section_text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
            continue  # separador
        rows.append(cells)
    return rows


# Allowlist explícita de artículos del pack por lado (I3). Los artículos de la
# UE son los 24 del índice de gdpr.md más los que aparecen en el crosswalk
# (p. ej. Arts. 51–59 y Art. 83 de la autoridad/sanciones). Los de Chile son
# los del índice de chile-21719.md más los del crosswalk, incluidos los
# artículos nuevos (bis/ter/quáter/quinquies/sexies) del texto modificado.
GDPR_ALLOWED_ARTICLES = {
    "2", "4", "5", "6", "7", "8", "9", "12", "13", "14", "15", "16", "17",
    "18", "20", "21", "22", "25", "26", "27", "28", "30", "32", "33", "34",
    "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46",
    "47", "48", "49", "51", "52", "53", "54", "55", "56", "57", "58", "59",
    "83",
}
CHILE_ALLOWED_ARTICLES = {
    "2", "4", "5", "6", "7", "8", "8bis", "8ter", "9", "10", "11", "12", "13",
    "14ter", "14quater", "14quinquies", "14sexies", "15ter", "16", "16bis",
    "16ter", "16quater", "27", "28", "29", "30", "30bis", "33", "34", "35",
    "36", "37", "38", "39", "48", "49", "50", "51", "52", "53", "54", "55",
}

ART_HEAD_RE = re.compile(r"Arts?\.?\s*", re.IGNORECASE)
ART_NUM_SUFFIX_RE = re.compile(
    r"(\d+)\s*°?\s*(bis|ter|qu[aá]ter|quinquies|sexies)?", re.IGNORECASE
)
ART_SEP_RE = re.compile(r"^\s*(?:,|/|y|and|–|-|hasta|a)\s*$", re.IGNORECASE)
ART_RANGE_SEP = {"–", "-", "hasta", "a"}


def _norm_suffix(suf: str | None) -> str:
    if not suf:
        return ""
    return _strip_accents(suf.lower().replace("á", "a").replace("é", "e")
                          .replace("í", "i").replace("ó", "o").replace("ú", "u"))


def extract_articles(cell: str) -> set[str]:
    """Artículos citados en una celda del crosswalk (con expansión de rangos)."""
    out: set[str] = set()
    for m in ART_HEAD_RE.finditer(cell):
        pos = m.end()
        items: list[tuple[str, str | None]] = []  # (token, sep_before)
        sep_before: str | None = None
        while True:
            nm = ART_NUM_SUFFIX_RE.match(cell, pos)
            if not nm:
                break
            token = nm.group(1) + _norm_suffix(nm.group(2))
            items.append((token, sep_before))
            pos = nm.end()
            sm = ART_SEP_RE.match(cell, pos)
            if not sm:
                break
            sep_before = sm.group(0).strip()
            pos = sm.end()
        prev_num: int | None = None
        for token, sep in items:
            out.add(token)
            base_m = re.match(r"(\d+)", token)
            if base_m and sep in ART_RANGE_SEP and prev_num is not None:
                a, b = prev_num, int(base_m.group(1))
                for n in range(min(a, b), max(a, b) + 1):
                    out.add(str(n))
            if base_m:
                prev_num = int(base_m.group(1))
    return out


def check_crosswalk(root: Path | None = None) -> list[str]:
    root = resolve_root(root)
    _, _, sources = _paths(root)
    failures: list[str] = []
    path = sources / "chile-eu-crosswalk.md"
    text = read_text(path)
    marker = '<a id="cw-tabla-1">'
    start = text.find(marker)
    if start == -1:
        return [f"  FALTA ancla {marker} en {path.relative_to(root)}"]
    rest = text[start:]
    nxt = rest.find('<a id="cw-tabla-2">')
    section = rest[:nxt] if nxt != -1 else rest
    rows = _table_rows(section)
    if len(rows) < 2:
        return ["  Tabla 1 sin filas parseables"]
    data = rows[1:]  # rows[0] = encabezado
    if len(data) != 13:
        failures.append(f"  Tabla 1 tiene {len(data)} filas de datos, se esperan 13")
    word_re = re.compile(r"\b(similar|ver|equivalente)\b", re.IGNORECASE)
    for i, cells in enumerate(data, 1):
        if len(cells) < 4:
            failures.append(f"  fila {i}: columnas insuficientes -> {cells}")
            continue
        num, dim, ue, cl = cells[0], cells[1], cells[2], cells[3]
        if str(i) != num.strip():
            failures.append(f"  fila {i}: numero de fila inesperado -> {num!r}")
        for label, cell in (("UE", ue), ("Chile", cl)):
            if not re.search(r"\d", cell):
                failures.append(f"  fila {i} ({dim}) columna {label}: sin numero/articulo -> {cell}")
            if word_re.search(cell) and not re.search(r"\d", cell):
                failures.append(
                    f"  fila {i} ({dim}) columna {label}: "
                    f"'similar/ver/equivalente' sin numero -> {cell}"
                )
        for label, cell, allowed in (
            ("UE", ue, GDPR_ALLOWED_ARTICLES),
            ("Chile", cl, CHILE_ALLOWED_ARTICLES),
        ):
            arts = extract_articles(cell)
            unknown = sorted(arts - allowed)
            if unknown:
                failures.append(
                    f"  fila {i} ({dim}) columna {label}: articulo(s) fuera "
                    f"de la allowlist del pack -> {unknown}"
                )
    return failures


# --- check 5: campos por obligacion ----------------------------------------
GDPR_FIELDS = ["Texto/cita", "Se operacionaliza en", "Determinismo", "Caveat"]
CHILE_FIELDS = ["Cita", "Se operacionaliza en", "Determinismo",
                "Diferencia con el GDPR", "Caveat"]

DETERMINISM_ENUM = ("DETERMINISTA", "SEMI", "JUICIO", "NO-VERIFICABLE-ESTATICAMENTE")

CITATION_MIN_LENGTH = 40
CITATION_TOO_SHORT = (
    "cita vacía o placeholder (menos de 40 caracteres): no es evidencia. "
    "El umbral de 40 es el mínimo para distinguir una cita textual real del "
    "marcador 'N/A', '(vacío)' o 'ver Art. X'."
)


def _has_field(body: str, name: str) -> bool:
    return re.search(r"\*\*" + re.escape(name) + r"\b", body) is not None


def _sections(path: Path, heading_re: re.Pattern[str]) -> list[tuple[str, str]]:
    """Devuelve [(titulo, contenido)] para headings que matchean."""
    text = read_text(path)
    lines = text.splitlines()
    idx = [i for i, l in enumerate(lines) if heading_re.match(l)]
    out = []
    for n, i in enumerate(idx):
        end = idx[n + 1] if n + 1 < len(idx) else len(lines)
        out.append((lines[i].strip(), "\n".join(lines[i:end])))
    return out


def _determinism_value(body: str) -> str | None:
    m = re.search(r"\*\*Determinismo:?\*\*\s*(.+)$", body, re.MULTILINE)
    return m.group(1).strip() if m else None


def _primary_determinism(value: str) -> str | None:
    norm = normalize(value).upper()
    best: str | None = None
    best_pos = len(norm) + 1
    for token in DETERMINISM_ENUM:
        pos = norm.find(normalize(token).upper())
        if pos != -1 and pos < best_pos:
            best_pos = pos
            best = token
    return best


# Nivel de determinismo que la doctrina asigna por artículo del pack.
# Refuerza el enum: un cambio que "suba" un JUICIO a DETERMINISTA se rechaza
# aunque el token sea válido (cierra la ruta T2→T5).
GDPR_EXPECTED_DETERMINISM = {
    "4": {"SEMI"},
    "5": {"DETERMINISTA", "SEMI"},
    "6": {"SEMI"},
    "7": {"SEMI"},
    "8": {"SEMI"},
    "9": {"SEMI"},
    "12": {"SEMI"},
    "13,14": {"SEMI"},
    "15": {"DETERMINISTA", "SEMI"},
    "16": {"DETERMINISTA"},
    "17": {"DETERMINISTA", "SEMI", "NO-VERIFICABLE-ESTATICAMENTE"},
    "18": {"SEMI"},
    "20": {"DETERMINISTA", "SEMI"},
    "21": {"DETERMINISTA", "SEMI"},
    "22": {"SEMI"},
    "25": {"JUICIO"},
    "28": {"DETERMINISTA", "SEMI"},
    "30": {"DETERMINISTA"},
    "32": {"SEMI"},
    "33,34": {"DETERMINISTA", "SEMI"},
    "35,36": {"SEMI", "JUICIO"},
    "44-49": {"SEMI"},
    "recital26": {"NO-VERIFICABLE-ESTATICAMENTE"},
    "recital71,4": {"SEMI"},
}

CHILE_EXPECTED_DETERMINISM = {
    "12": {"SEMI"},
    "13": {"SEMI"},
    "14ter": {"DETERMINISTA"},
    "15ter": {"SEMI"},
    "16": {"SEMI"},
    "16ter": {"SEMI"},
    "16quater": {"SEMI"},
    "8ter": {"DETERMINISTA"},
    "8bis": {"SEMI"},
    "barsop": {"DETERMINISTA"},
    "14sexies": {"SEMI"},
    "14quater,14quinquies": {"DETERMINISTA", "JUICIO"},
    "27,28,29": {"SEMI"},
    "30,30bis": {"NO-VERIFICABLE-ESTATICAMENTE"},
}


def gdpr_heading_key(title: str) -> str:
    """'## GDPR Art. 25 — X' → '25'; '## GDPR Arts. 44–49 — X' → '44-49'."""
    if "Recital 71" in title:
        return "recital71,4"
    if "Recital 26" in title:
        return "recital26"
    m = re.search(r"Art(?:s)?\.?\s*(.+?)\s*—", title)
    part = m.group(1) if m else ""
    nums = re.findall(r"\d+", part)
    if not nums:
        return ""
    if len(nums) == 2 and re.search(r"–|-", part):
        return f"{nums[0]}-{nums[1]}"
    return ",".join(nums)


def chile_heading_key(title: str) -> str:
    """'## Ley 19.628 ... — Art. 14 ter — X' → '14ter'."""
    if "Catálogo de derechos" in title:
        return "barsop"
    m = re.search(r"—\s*(.+?)\s*—", title)
    part = m.group(1) if m else ""
    tokens = []
    for mm in re.finditer(r"(\d+)\s*°?\s*(bis|ter|qu[aá]ter|quinquies|sexies)?", part, re.I):
        tokens.append(mm.group(1) + _norm_suffix(mm.group(2)))
    return ",".join(tokens)


def _validate_citation(failures: list[str], label: str, body: str, name: str) -> None:
    m = re.search(
        r"\*\*(?:texto/)?cita[^:*]*:?\*\*\s*(.+)$",
        body, re.IGNORECASE | re.MULTILINE,
    )
    if not m:
        failures.append(f"  {label}: falta campo {name}")
        return
    raw = re.sub(r"[*`_]", "", m.group(1)).strip()
    if len(raw) < CITATION_MIN_LENGTH:
        failures.append(
            f"  {label}: {name} demasiado corta ({len(raw)} < "
            f"{CITATION_MIN_LENGTH}) — {raw!r}"
        )


def _validate_determinism(
    failures: list[str], label: str, value: str | None,
    key: str, expected: set[str] | None,
) -> None:
    if value is None:
        failures.append(f"  {label}: falta el valor de Determinismo")
        return
    primary = _primary_determinism(value)
    if primary is None:
        failures.append(f"  {label}: Determinismo fuera del enum -> {value!r}")
        return
    if expected is None:
        failures.append(f"  {label}: artículo {key!r} sin nivel esperado en doctrina")
        return
    if primary not in expected:
        failures.append(
            f"  {label}: Determinismo {primary} incoherente con doctrina "
            f"(esperado: {sorted(expected)})"
        )


def check_fields(root: Path | None = None) -> list[str]:
    root = resolve_root(root)
    _, _, sources = _paths(root)
    failures: list[str] = []

    gdpr_path = sources / "gdpr.md"
    gdpr_text = read_text(gdpr_path)
    if not gdpr_text:
        failures.append("  GDPR: no se encontró sources/gdpr.md")
    elif not re.search(r'Diferencia con el GDPR"?:\s*\**\s*NO aplica', gdpr_text, re.IGNORECASE):
        failures.append(
            "  GDPR: falta la declaracion explicita de que el campo "
            "'Diferencia con el GDPR' NO aplica (hueco silencioso)."
        )
    gdpr_head = re.compile(r"^##\s+GDPR\s+(?:Art|Arts|Recital)\b")
    gdpr_sections = _sections(gdpr_path, gdpr_head)
    if gdpr_text and not gdpr_sections:
        failures.append("  GDPR: no se encontró ninguna obligación (¿headings renombrados?)")
    for title, body in gdpr_sections:
        missing = [f for f in GDPR_FIELDS if not _has_field(body, f)]
        if missing:
            failures.append(f"  GDPR [{title}]: faltan campos {missing}")
        _validate_citation(failures, f"GDPR [{title}]", body, "Texto/cita")
        key = gdpr_heading_key(title)
        _validate_determinism(
            failures, f"GDPR [{title}]", _determinism_value(body),
            key, GDPR_EXPECTED_DETERMINISM.get(key),
        )

    cl_path = sources / "chile-21719.md"
    cl_text = read_text(cl_path)
    cl_head = re.compile(r"^##\s+Ley 19\.628\b")
    cl_sections = _sections(cl_path, cl_head)
    if cl_text and not cl_sections:
        failures.append("  Chile: no se encontró ninguna obligación (¿headings renombrados?)")
    for title, body in cl_sections:
        missing = [f for f in CHILE_FIELDS if not _has_field(body, f)]
        if missing:
            failures.append(f"  Chile [{title}]: faltan campos {missing}")
        _validate_citation(failures, f"Chile [{title}]", body, "Cita")
        key = chile_heading_key(title)
        _validate_determinism(
            failures, f"Chile [{title}]", _determinism_value(body),
            key, CHILE_EXPECTED_DETERMINISM.get(key),
        )

    return failures


# --- check 7: obligations.json (extractor mecánico ya corrido) --------------
# Valida el resultado de scripts/build_obligations.py, que es la fuente de
# verdad para los detectores futuros. El control nuclear: un determinismo
# `JUICIO` o `NO-VERIFICABLE-ESTATICAMENTE` nunca puede declarar `SATISFIED`
# (doctrine.md:135-145).
OBLIGATIONS_JSON = "obligations.json"
OBLIGATIONS_MIN = 30

DETERMINISM_TECHO = {
    "DETERMINISTA": "SATISFIED",
    "SEMI": "PARTIAL",
    "JUICIO": "PARTIAL",
    "NO-VERIFICABLE-ESTATICAMENTE": "NO_CONCLUIBLE_ESTATICAMENTE",
}
RESPONSABLE_DETERMINISMO_PROHIBIDO_SATISFIED = ("JUICIO", "NO-VERIFICABLE-ESTATICAMENTE")


def check_obligations(root: Path | None = None) -> list[str]:
    root = resolve_root(root)
    _, refs, _ = _paths(root)
    failures: list[str] = []
    path = refs / "obligations" / OBLIGATIONS_JSON

    if not path.is_file():
        return [
            f"  FALTA {path.relative_to(root)}: el pack de obligaciones "
            "generado no existe (correr scripts/build_obligations.py)"
        ]
    try:
        data = json.loads(read_text(path))
    except ValueError as exc:
        return [f"  INVALID JSON {path.relative_to(root)}: {exc}"]

    if not isinstance(data, list):
        return [
            f"  {path.relative_to(root)}: se espera una lista de fichas, "
            f"se obtuvo {type(data).__name__}"
        ]
    if len(data) < OBLIGATIONS_MIN:
        failures.append(
            f"  {path.relative_to(root)}: {len(data)} fichas < mínimo "
            f"{OBLIGATIONS_MIN} (truncado o generación rota)"
        )

    seen_ids: dict[str, int] = {}
    for i, ficha in enumerate(data):
        label = f"obligacion[{i}]"
        if not isinstance(ficha, dict):
            failures.append(f"  {label}: no es un objeto -> {ficha!r}")
            continue

        fid = ficha.get("id")
        if not isinstance(fid, str) or not fid.strip():
            failures.append(f"  {label}: id ausente o inválido -> {fid!r}")
        else:
            seen_ids[fid] = seen_ids.get(fid, 0) + 1

        det_raw = ficha.get("determinismo")
        if not isinstance(det_raw, str) or not det_raw.strip():
            failures.append(
                f"  {label}: determinismo ausente o inválido -> {det_raw!r}"
            )
            continue
        primary = _primary_determinism(det_raw)
        if primary is None:
            failures.append(
                f"  {label} ({fid or '?'}): determinismo fuera del enum "
                f"(doctrine.md) -> {det_raw!r}"
            )
            continue

        techo = ficha.get("techo_de_veredicto")
        expected = DETERMINISM_TECHO.get(primary)
        if techo != expected:
            failures.append(
                f"  {label} ({fid or '?'}): techo_de_veredicto {techo!r} "
                f"incoherente con determinismo {primary!r} (esperado "
                f"{expected!r})"
            )
        if primary in RESPONSABLE_DETERMINISMO_PROHIBIDO_SATISFIED and techo == "SATISFIED":
            failures.append(
                f"  {label} ({fid or '?'}): CONTROL NUCLEAR — determinismo "
                f"{primary} no puede declarar SATISFIED (techo máximo "
                f"PARTIAL / NO_CONCLUIBLE_ESTATICAMENTE)"
            )

    for fid, n in sorted((k, v) for k, v in seen_ids.items() if v > 1):
        failures.append(f"  id duplicado: {fid!r} aparece {n} veces")
    return failures


# --- check 6: hash del pack -------------------------------------------------
def check_hash(root: Path | None = None) -> list[str]:
    root = resolve_root(root)
    _, refs, sources = _paths(root)
    failures: list[str] = []
    manifest = sources / "SOURCES.sha256"
    if not manifest.is_file():
        return [f"  FALTA manifiesto de integridad: {manifest.relative_to(root)}"]

    listed: set[Path] = set()
    for lineno, raw in enumerate(read_text(manifest).splitlines(), 1):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"^([0-9a-fA-F]{64})\s+\*?(.+?)\*?\s*$", s)
        if not m:
            failures.append(f"  manifiesto:{lineno}: formato inválido -> {raw!r}")
            continue
        expected, rel = m.group(1).lower(), m.group(2).strip()
        target = (refs / rel).resolve()
        listed.add(target)
        if not target.is_file():
            failures.append(f"  HASH {rel}: archivo listado no existe")
            continue
        got = sha256(target)
        if got != expected:
            failures.append(
                f"  HASH {rel}: esperado {expected} obtenido {got}"
            )

    # Activo fuera del manifiesto: un archivo en references/sources/ que no
    # está cubierto por un hash es un activo desprotegido (mitiga T2).
    if sources.is_dir():
        for p in sorted(sources.rglob("*")):
            if not p.is_file() or p.resolve() == manifest.resolve():
                continue
            if p.resolve() not in listed:
                failures.append(
                    f"  NO LISTADO {p.relative_to(root)}: archivo en "
                    "references/sources/ fuera del manifiesto"
                )
    return failures


# --- runner -----------------------------------------------------------------
CHECKS = {
    1: ("Anclas e indices", check_anchors),
    2: ("Contaminacion (frases prohibidas)", check_contamination),
    3: ("Conteo de palabras", check_wordcount),
    4: ("Crosswalk Tabla 1 (13 filas + allowlist)", check_crosswalk),
    5: ("Campos por obligacion y determinismo", check_fields),
    6: ("Integridad del pack (SHA-256)", check_hash),
    7: ("Obligations generadas (determinismo->techo + control nuclear)",
        check_obligations),
}


def main(argv: list[str]) -> int:
    try:
        root = resolve_root()
    except RootError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1
    selected = sorted(CHECKS) if len(argv) == 1 else [int(a) for a in argv[1:]]
    failed = 0
    for n in selected:
        if n not in CHECKS:
            print(f"[check {n}] inexistente")
            failed += 1
            continue
        name, fn = CHECKS[n]
        print(f"\n===== CHECK {n} — {name} =====")
        if n == 2:
            legit, flags = fn(root)
            print(f"  {len(legit)} coincidencias legitimas (doctrina/❌):")
            for r in legit:
                print(r)
            if flags:
                print(f"  {len(flags)} FLAGS a revisar:")
                for r in flags:
                    print(r)
                failed += 1
            else:
                print("  OK: ninguna aparicion como afirmacion.")
        elif n == 3:
            for r in fn(root):
                print(r)
        else:
            problems = fn(root)
            if problems:
                print(f"  FALLOS ({len(problems)}):")
                for r in problems:
                    print(r)
                failed += 1
            else:
                print("  OK")
    print(f"\nResultado: {'FALLO' if failed else 'OK'} "
          f"(checks con problemas: {failed})")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
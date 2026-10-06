#!/usr/bin/env python3
"""build_obligations.py — extractor mecánico de fichas de obligaciones.

Genera `references/obligations/` (obligations.json, index.md,
PENDING_VIGENCIA.md) a partir de las fichas estructuradas de los archivos de
fuentes del pack (`gdpr.md`, `eprivacy.md`, `chile-21719.md`).

Principios:
  - No escribe las fichas a mano: todo se extrae de las fuentes por
    estructura (heading de la obligación + campos etiquetados que la siguen).
  - Tolerante a variaciones de heading (`## GDPR Art. 25 — Título` vs
    `## Ley 19.628 (mod. Ley 21.719) — Art. 16 quáter — Título`) y de etiqueta
    (`**Texto/cita:**` vs `**Cita:**`). El número del artículo se extrae del
    propio heading con regex, nunca se hardcodea la lista de artículos.
  - Fallo ruidoso: si se extraen menos de MIN_FICHAS fichas (esperado >= 35)
    o una ficha no parsea, aborta con error — no escribe un JSON vacío.
  - Control nuclear: mapea determinismo -> techo_de_veredicto según
    doctrine.md §§ Niveles de determinismo / Regla del techo de veredicto.
    Un `JUICIO` jamás puede emitir `SATISFIED`. Si el determinismo de una
    ficha no está en el enum, falla.

Solo stdlib, sin red, determinista: mismo input -> mismo output (no lleva
timestamp). Uso:
    python3 build_obligations.py
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

# --- rutas -----------------------------------------------------------------
# <root>/skills/legal-audit/scripts/build_obligations.py
SCRIPT = Path(__file__).resolve()
SKILL_DIR = SCRIPT.parents[1]           # skills/legal-audit
REFERENCES = SKILL_DIR / "references"
SOURCES = REFERENCES / "sources"
OUT_DIR = REFERENCES / "obligations"

# --- parámetros ------------------------------------------------------------
# Umbral mínimo razonable de fichas. El pack real tiene 24 (GDPR) + 1
# (ePrivacy) + 14 (Chile) = 39. Si el parser devuelve menos, está roto y
# tiene que gritar, no escribir un archivo vacío.
MIN_FICHAS = 35

DETERMINISM_ENUM = (
    "DETERMINISTA",
    "SEMI",
    "JUICIO",
    "NO-VERIFICABLE-ESTATICAMENTE",
)

# Mapeo determinismo -> techo máximo de veredicto (doctrine.md:118-145
# "Niveles de determinismo" + "Regla del techo de veredicto").
TECHO_POR_DETERMINISMO = {
    "DETERMINISTA": "SATISFIED",
    "SEMI": "PARTIAL",
    "JUICIO": "PARTIAL",
    "NO-VERIFICABLE-ESTATICAMENTE": "NO_CONCLUIBLE_ESTATICAMENTE",
}

# Qué tiene que producir la evidencia según el determinismo.
RESPONSABLE_POR_DETERMINISMO = {
    "DETERMINISTA": "DETECTOR",          # hay un check automatizado
    "SEMI": "AMBOS",                     # parte determinista + parte contextual
    "JUICIO": "JUICIO-HUMANO",           # interpretación humana/LLM
    "NO-VERIFICABLE-ESTATICAMENTE": "JUICIO-HUMANO",
}

# Las fichas UE son el lado de referencia: el campo "Diferencia con el GDPR"
# NO aplica por definición (declarado en sources/gdpr.md). La comparación vive
# en sources/chile-eu-crosswalk.md.
UE_DIFERENCIA_NOTA = (
    "NO APLICA: ficha del lado UE (referencia); la comparación con Chile vive "
    "en sources/chile-eu-crosswalk.md (declarado en sources/gdpr.md)."
)

VIGENCIA_DEFAULT = "2026-12-01"
BOLETIN_POSTERGACION = (
    "PUBLICADA, NO VIGENTE — posible postergación a 2027-12-01 "
    "(Boletín 18.623-07, en tramitación; no es ley)"
)

# --- normalización (espejo de verify_pack.py) ------------------------------
_OPERATOR_TOKENS = {"≠": " neq ", "≥": " ge ", "≤": " le ", "=": " eq "}


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


def normalize(text: str) -> str:
    t = text.lower()
    for op, tok in _OPERATOR_TOKENS.items():
        t = t.replace(op, tok)
    t = _strip_accents(t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _primary_determinism(value: str) -> str | None:
    """Determinismo principal de un valor (compuesto o no): el token del enum
    que aparece PRIMERO en el texto normalizado. Espejo de
    verify_pack.py:_primary_determinism para que el generador y el verificador
    estén de acuerdo sobre la misma ficha."""
    norm = normalize(value).upper()
    best: str | None = None
    best_pos = len(norm) + 1
    for token in DETERMINISM_ENUM:
        pos = norm.find(normalize(token).upper())
        if pos != -1 and pos < best_pos:
            best_pos = pos
            best = token
    return best


# --- reconocimiento estructural --------------------------------------------
# Una ficha es: un heading de obligación + los campos etiquetados que siguen.
GDPR_HEADING_RE = re.compile(r"^##\s+GDPR\s+(.+?)\s*—\s*(.+?)\s*$")
EPRIVACY_HEADING_RE = re.compile(
    r"^##\s+Directiva 2002/58/EC\s+Art\.\s*5\(3\)\s*(.*)$"
)
CHILE_HEADING_RE = re.compile(r"^##\s+Ley 19\.628\b(.*?)—\s*(.+?)\s*—\s*(.+?)\s*$")

ANY_HEADING_RE = re.compile(r"^#{1,6}\s")
BULLET_RE = re.compile(r"^\s*-\s*\*\*\s*([^*:]+?)\s*:?\s*\*\*\s*(.*)$")
CAPTURA_RE = re.compile(r"\*\*Fecha de captura:\*\*\s*(\d{4}-\d{2}-\d{2})")
VIGENCIA_RE = re.compile(r"entrada en vigencia esperada \*\*(\d{4}-\d{2}-\d{2})\*\*")

# etiqueta -> campo. Se hace match normalizado para absorber variaciones:
# `**Texto/cita:**`, `**Cita:**`, `**Cita (Art. 4):**`, `**Diferencia con el GDPR:**`.
_FIELD_PREFIXES = (
    ("texto/cita", "cita"),
    ("cita", "cita"),
    ("se operacionaliza en", "operacionalizacion"),
    ("determinismo", "determinismo"),
    ("caveat", "caveat"),
    ("diferencia con el gdpr", "diferencia"),
)

SUFFIX_RANK = {
    "": 0, "bis": 1, "ter": 2, "quater": 3, "quinquies": 4, "sexies": 5,
}


def _norm_label(raw: str) -> str:
    s = re.sub(r"[^a-z0-9/ ]", "", raw.lower())
    return re.sub(r"\s+", " ", s).strip()


def _field_for_label(label: str) -> str | None:
    lab = _norm_label(label)
    for prefix, field in _FIELD_PREFIXES:
        if lab.startswith(prefix):
            return field
    return None


def _norm_suffix(suf: str) -> str:
    return _strip_accents(suf.lower())


def _sections(text: str, heading_re: re.Pattern[str]) -> list[tuple[str, list[str]]]:
    """[(heading, body_lines)] para cada heading que matchea. El cuerpo de la
    ficha termina en el próximo heading de CUALQUIER nivel: evita que una
    sección de jurisprudencia o una subsección se cuele como campo de la
    última ficha (p. ej. los `- **Determinismo:**` de WP29 tras el Recital 71)."""
    out: list[tuple[str, list[str]]] = []
    cur: tuple[str, list[str]] | None = None
    for line in text.splitlines():
        if heading_re.match(line):
            if cur is not None:
                out.append(cur)
            cur = (line.strip(), [])
        elif cur is not None:
            if ANY_HEADING_RE.match(line):
                out.append(cur)
                cur = None
            else:
                cur[1].append(line)
    if cur is not None:
        out.append(cur)
    return out


def _parse_fields(body: list[str]) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in body:
        m = BULLET_RE.match(line)
        if not m:
            continue
        field = _field_for_label(m.group(1))
        if field is None:
            continue
        value = m.group(2).strip()
        if field not in fields:
            fields[field] = value  # primer bullet con esa etiqueta
    return fields


def _extract_captura(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    m = CAPTURA_RE.search(text)
    if not m:
        raise ValueError(f"{path.name}: sin '**Fecha de captura:**' verificable")
    return m.group(1)


# --- ids -------------------------------------------------------------------
def _gdpr_id(art_part: str) -> str:
    if "Recital 71" in art_part:
        return "gdpr-recital-71-art-4"
    if "Recital 26" in art_part:
        return "gdpr-recital-26"
    tokens = re.findall(r"\d+", art_part)
    if not tokens:
        raise ValueError(f"GDPR: sin número de artículo en {art_part!r}")
    return "gdpr-art-" + "-".join(tokens)


def _eprivacy_id() -> str:
    return "eprivacy-art-5-3"


def _chile_id(heading: str, art_part: str) -> str:
    if "Catálogo de derechos" in heading:
        return "cl-barsop"
    tokens = []
    for m in re.finditer(
        r"(\d+)\s*°?\s*(bis|ter|qu[aá]ter|quinquies|sexies)?", art_part, re.I
    ):
        base, suf = m.group(1), (m.group(2) or "")
        tokens.append(base + (("-" + _norm_suffix(suf)) if suf else ""))
    if not tokens:
        raise ValueError(f"Chile: sin número de artículo en {art_part!r}")
    return "cl-" + "-".join(tokens)


# --- construcción de la ficha ----------------------------------------------
def _build_ficha(
    *,
    heading: str,
    body: list[str],
    jurisdiccion: str,
    articulo: str,
    titulo: str,
    source_rel: str,
    captura: str,
    require_diferencia: bool,
    fid: str,
) -> dict:
    fields = _parse_fields(body)
    required = ["cita", "operacionalizacion", "determinismo", "caveat"]
    missing = [f for f in required if f not in fields]
    if missing:
        raise ValueError(
            f"{source_rel}: ficha {heading!r} sin campos {missing}"
        )
    if require_diferencia and "diferencia" not in fields:
        raise ValueError(
            f"{source_rel}: ficha {heading!r} sin campo 'Diferencia con el GDPR'"
        )

    det_raw = fields["determinismo"]
    primary = _primary_determinism(det_raw)
    if primary is None:
        raise ValueError(
            f"{source_rel}: ficha {heading!r}: Determinismo fuera del enum -> "
            f"{det_raw!r}"
        )
    if primary not in TECHO_POR_DETERMINISMO:
        raise ValueError(
            f"{source_rel}: ficha {heading!r}: determinismo {primary!r} sin "
            "techo mapeado (falla el enum)"
        )

    ficha: dict = {
        "id": fid,
        "jurisdiccion": jurisdiccion,
        "articulo": articulo,
        "titulo": titulo,
        "fuente": source_rel,
        "captura": captura,
        "cita": fields["cita"],
        "operacionalizacion": fields["operacionalizacion"],
        "determinismo": det_raw,
        "determinismo_principal": primary,
        "techo_de_veredicto": TECHO_POR_DETERMINISMO[primary],
        "responsable": RESPONSABLE_POR_DETERMINISMO[primary],
        "caveat": fields["caveat"],
        "diferencia_con_gdpr": fields.get("diferencia"),
    }
    if jurisdiccion == "UE":
        ficha["diferencia_con_gdpr_nota"] = UE_DIFERENCIA_NOTA
    return ficha


# --- parsing por archivo ----------------------------------------------------
def parse_gdpr() -> list[dict]:
    path = SOURCES / "gdpr.md"
    text = path.read_text(encoding="utf-8")
    captura = _extract_captura(path)
    fichas = []
    for heading, body in _sections(text, GDPR_HEADING_RE):
        m = GDPR_HEADING_RE.match(heading)
        art_part, titulo = m.group(1).strip(), m.group(2).strip()
        ficha = _build_ficha(
            heading=heading,
            body=body,
            jurisdiccion="UE",
            articulo=art_part,
            titulo=titulo,
            source_rel="references/sources/gdpr.md",
            captura=captura,
            require_diferencia=False,
            fid=_gdpr_id(art_part),
        )
        fichas.append(ficha)
    return fichas


def parse_eprivacy() -> list[dict]:
    path = SOURCES / "eprivacy.md"
    text = path.read_text(encoding="utf-8")
    captura = _extract_captura(path)
    fichas = []
    for heading, body in _sections(text, EPRIVACY_HEADING_RE):
        m = EPRIVACY_HEADING_RE.match(heading)
        titulo = m.group(1).strip() or "Art. 5(3)"
        ficha = _build_ficha(
            heading=heading,
            body=body,
            jurisdiccion="UE",
            articulo="Art. 5(3)",
            titulo=titulo,
            source_rel="references/sources/eprivacy.md",
            captura=captura,
            require_diferencia=False,
            fid=_eprivacy_id(),
        )
        fichas.append(ficha)
    return fichas


def parse_chile() -> tuple[list[dict], str]:
    path = SOURCES / "chile-21719.md"
    text = path.read_text(encoding="utf-8")
    captura = _extract_captura(path)
    vm = VIGENCIA_RE.search(text)
    vigencia = vm.group(1) if vm else VIGENCIA_DEFAULT
    fichas = []
    for heading, body in _sections(text, CHILE_HEADING_RE):
        m = CHILE_HEADING_RE.match(heading)
        ley_part, art_part, titulo = (
            m.group(1).strip(), m.group(2).strip(), m.group(3).strip(),
        )
        if not ley_part:
            raise ValueError(f"chile-21719.md: ficha {heading!r} sin 'Ley 19.628 (mod. Ley 21.719)'")
        ficha = _build_ficha(
            heading=heading,
            body=body,
            jurisdiccion="CL",
            articulo=art_part,
            titulo=titulo,
            source_rel="references/sources/chile-21719.md",
            captura=captura,
            require_diferencia=True,
            fid=_chile_id(heading, art_part),
        )
        fichas.append(ficha)
    return fichas, vigencia


# --- salidas ----------------------------------------------------------------
def _esc_md(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


def _sort_key(ficha: dict) -> tuple:
    art = ficha["articulo"]
    m = re.search(r"(\d+)", art)
    num = int(m.group(1)) if m else 0
    ms = re.search(r"(\d+)\s*°?\s*(bis|ter|qu[aá]ter|quinquies|sexies)?", art, re.I)
    suf = _norm_suffix(ms.group(2)) if ms and ms.group(2) else ""
    return (
        0 if ficha["jurisdiccion"] == "UE" else 1,
        num,
        SUFFIX_RANK.get(suf, 99),
        art,
    )


def write_obligations(fichas: list[dict]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "obligations.json"
    path.write_text(
        json.dumps(fichas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path


def write_index(fichas: list[dict], counts: dict[str, int]) -> Path:
    lines = [
        "# Índice de obligaciones",
        "",
        "Generado mecánicamente por `scripts/build_obligations.py` a partir de",
        "las fichas estructuradas de `references/sources/` (gdpr.md, eprivacy.md,",
        "chile-21719.md). No editar a mano: se regenera con el script.",
        "",
        "`obligations.json` es la fuente de verdad para los detectores.",
        "",
        f"Total: {len(fichas)} fichas "
        f"(GDPR {counts.get('gdpr', 0)} · ePrivacy {counts.get('eprivacy', 0)} · "
        f"Chile {counts.get('chile', 0)}).",
        "",
        "- Un `determinismo` compuesto (p. ej. ",
        "  `DETERMINISTA en estructura ..., SEMI en suficiencia`) se muestra en",
        "  la tabla como su determinismo principal (`determinismo_principal`).",
        "- `diferencia_con_gdpr` es `null` en las fichas UE por definición: son",
        "  el lado de referencia; la comparación con Chile vive en",
        "  `sources/chile-eu-crosswalk.md`.",
        "- El `techo_de_veredicto` es el máximo que doctrine.md permite para el",
        "  determinismo de la ficha: un `JUICIO` o `NO-VERIFICABLE-ESTATICAMENTE`",
        "  nunca puede emitir `SATISFIED` (regla del techo de veredicto).",
        "",
        "| id | jurisdicción | artículo | título | determinismo | techo | responsable |",
        "|----|--------------|----------|--------|--------------|-------|-------------|",
    ]
    for f in sorted(fichas, key=_sort_key):
        titulo = f["titulo"]
        if len(titulo) > 64:
            titulo = titulo[:61] + "..."
        lines.append(
            f"| {_esc_md(f['id'])} | {_esc_md(f['jurisdiccion'])} | "
            f"{_esc_md(f['articulo'])} | {_esc_md(titulo)} | "
            f"{_esc_md(f['determinismo_principal'])} | "
            f"{_esc_md(f['techo_de_veredicto'])} | {_esc_md(f['responsable'])} |"
        )
    lines.append("")
    path = OUT_DIR / "index.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_pending_vigencia(fichas_cl: list[dict], vigencia: str) -> Path:
    lines = [
        "# Obligaciones chilenas pendientes de vigencia",
        "",
        "La Ley 19.628 (mod. Ley 21.719) está **PUBLICADA pero NO VIGENTE** al",
        "2026-10-05 (fuente: `sources/chile-21719.md`, sección Vigencia).",
        "Mientras tanto rige la Ley 19.628 antigua.",
        "",
        f"**Entrada en vigor:** {vigencia} (Art. primero transitorio de la Ley",
        "21.719: \"el día primero del mes vigésimo cuarto posterior a la",
        "publicación\").",
        "",
        "**Postergación pendiente:** el Boletín 18.623-07 (en tramitación en el",
        "Senado, suma urgencia; **no es ley** al momento de captura) propone",
        "postergar la vigencia al **2027-12-01**. Hasta que se publique en el",
        f"D.O., la fecha exigible sigue siendo {vigencia}.",
        "",
        "La skill NO emite veredictos de cumplimiento sobre estas obligaciones:",
        "debe reportarlas como `PENDING_VIGENCIA`, con la fecha de entrada en",
        "vigor explícita (ver `doctrine.md`).",
        "",
        "| id | artículo | título | entrada en vigor | estado |",
        "|----|----------|--------|------------------|--------|",
    ]
    for f in sorted(fichas_cl, key=_sort_key):
        titulo = f["titulo"]
        if len(titulo) > 56:
            titulo = titulo[:53] + "..."
        lines.append(
            f"| {_esc_md(f['id'])} | {_esc_md(f['articulo'])} | "
            f"{_esc_md(titulo)} | {vigencia} | {BOLETIN_POSTERGACION} |"
        )
    lines.append("")
    path = OUT_DIR / "PENDING_VIGENCIA.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main(argv: list[str]) -> int:
    gdpr = parse_gdpr()
    eprivacy = parse_eprivacy()
    chile, vigencia = parse_chile()
    fichas = gdpr + eprivacy + chile

    counts = {"gdpr": len(gdpr), "eprivacy": len(eprivacy), "chile": len(chile)}

    print(f"gdpr.md:       {counts['gdpr']:>2} fichas")
    print(f"eprivacy.md:   {counts['eprivacy']:>2} fichas")
    print(f"chile-21719.md:{counts['chile']:>3} fichas")
    print(f"TOTAL:         {len(fichas):>3} fichas")

    if len(fichas) < MIN_FICHAS:
        print(
            f"\nERROR: se extrajeron {len(fichas)} fichas (< umbral {MIN_FICHAS}). "
            "El parser está roto o las fuentes cambiaron; no se escribe "
            "obligations.json.",
            file=sys.stderr,
        )
        return 1

    ids = [f["id"] for f in fichas]
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        print(
            f"\nERROR: ids duplicados -> {dupes}. No se escribe obligations.json.",
            file=sys.stderr,
        )
        return 1

    p1 = write_obligations(fichas)
    p2 = write_index(fichas, counts)
    p3 = write_pending_vigencia(chile, vigencia)
    print(f"\nEscribí:\n  {p1}\n  {p2}\n  {p3}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
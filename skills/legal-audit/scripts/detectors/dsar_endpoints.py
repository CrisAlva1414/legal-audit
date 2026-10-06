#!/usr/bin/env python3
"""D3 — dsar_endpoints.py · DETERMINISTA → Arts. 15, 16, 17, 18, 20, 21

Verifica la existencia de mecanismos de derechos (Personal Data Subject
Access Rights): acceso+export, rectificación, supresión, portabilidad,
oposición y restricción; y distingue borrado real de soft-delete.

Hechos emitidos (nunca juicios):
    - presencia: "se encontró mecanismo/menciones de <derecho> en f:l";
    - ausencia: "no se ha encontrado <derecho> en el repositorio" (f:0);
    - borrado por soft-delete vs hard-delete y propagación a backups/caches.

La presencia se marca en dos niveles: coincidencia fuerte (contexto de
rutas/endpoints/servicios) y débil (cualquier mención). Un derecho con cero
coincidencias produce un hecho de ausencia (archivo ".", linea 0) — ese
hecho es lo que el subagente cita para un veredicto.

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

DETECTOR = "dsar_endpoints"
COVERED_OBLIGACIONES = {
    "gdpr-art-15", "gdpr-art-16", "gdpr-art-17",
    "gdpr-art-18", "gdpr-art-20", "gdpr-art-21",
}

# Contexto que sugiere ruta/endpoint/servicio (para la coincidencia fuerte).
_ROUTE_CTX_RE = compile_alt([
    r"@app\.route", r"@router\.", r"@api\.", r"app\.(?:get|post|put|delete|patch)\s*\(",
    r"router\.(?:get|post|put|delete|patch)\s*\(", r"add_url_rule", r"path\s*\(",
    r"url\s*\(", r"(?:get|post|put|delete)Mapping", r"@(?:get|post|put|delete|request|action)\b",
    r"(?:def|async def)\s+\w*(?:export|delete|erase|remove|access|rectif|object|opt|portab|restric|download|supres|borrar)[\w]*\s*\(",
    r"(?:class|const|let|var|function)\s+\w*(?:controller|service|handler|repository|gateway|api|endpoint|resolver|command|cli)\w*",
    r"\b(app|api|router|server|handler)\.", r"\b(handle|execute|process|run)\s*\(",
])

# (id, nombre corto, patrones DÉBILES (cualquier mención), patrones FUERTES (contexto ruta))
RIGHTS = [
    {
        "obligacion": "gdpr-art-15",
        "nombre": "acceso y exportación (Art. 15)",
        "weak": compile_alt([
            r"\bsar\b", r"subject_?access", r"data_?request", r"data_?export",
            r"export_?data", r"access_(?:data|info|user|account|profile|record)",
            r"data_?access", r"my_?data", r"get_?my",
            r"consulta\w*(?:datos|personal)", r"acceso\w*(?:datos|personal)",
            r"descargar", r"request_?data", r"access_right",
        ]),
        "strong": compile_alt([
            r"(?:export|export_?data|data_?export|download|my_?data|get_?my|access|sar|data_?subject)",
        ]),
    },
    {
        "obligacion": "gdpr-art-16",
        "nombre": "rectificación (Art. 16)",
        "weak": compile_alt([
            r"rectif", r"corrige|corregir", r"update_?(?:user|profile|account|email|phone|name)",
            r"edit_?(?:profile|user|account)|edit\b", r"modific", r"change_?(?:email|phone|name|user)",
            r"actualiz\w*profil", r"actualizar.*datos",
        ]),
        "strong": compile_alt([r"rectif|corrige|corregir|update_?(?:user|profile|account|email|phone)|edit_?(?:profile|account)"]),
    },
    {
        "obligacion": "gdpr-art-17",
        "nombre": "supresión/borrado (Art. 17)",
        "weak": compile_alt([
            r"\bdelete\b", r"\berase\b", r"\bremove\b", r"borrar", r"supres",
            r"purge", r"hard_?delete", r"\bdestroy\b", r"forget\b", r"olvido",
            r"delete_?account", r"close_?account", r"deregister", r"baja\w*(?:datos|lógica)",
        ]),
        "strong": compile_alt([r"\bdelete\b|\berase\b|\bremove\b|borrar|supres|hard_?delete|\bdestroy\b|delete_?account"]),
    },
    {
        "obligacion": "gdpr-art-18",
        "nombre": "restricción (Art. 18)",
        "weak": compile_alt([
            r"restric", r"restrict", r"pause\w*process", r"suspend", r"suspende",
            r"block_?processing", r"\bfreeze\b", r"\bhold\b", r"restriction\w*data",
        ]),
        "strong": compile_alt([r"restric|restrict|block_?processing|suspend\w*(?:process|data|user)|pause_?process"]),
    },
    {
        "obligacion": "gdpr-art-20",
        "nombre": "portabilidad (Art. 20)",
        "weak": compile_alt([
            r"portab", r"portability", r"export_?(?:json|csv|archive|data)", r"json_?export",
            r"csv_?export", r"download_?(?:data|archive)", r"data_?export", r"machine_?readable",
            r"get_?data_?dump", r"export\w*estructurad",
        ]),
        "strong": compile_alt([r"portab|portability|export_?(?:json|csv|archive|data)|data_?export|json_?export|csv_?export|download_?(?:data|archive)"]),
    },
    {
        "obligacion": "gdpr-art-21",
        "nombre": "oposición/opt-out (Art. 21)",
        "weak": compile_alt([
            r"opt_?out", r"\boptout\b", r"\bobjection\b", r"oposicion", r"opposition",
            r"unsubscribe", r"do_?not_?sell", r"\bsuppress\b", r"excluir",
            r"no_?contact", r"retirar\w*consentimiento", r"right.?to.?object",
        ]),
        "strong": compile_alt([r"opt_?out|oposicion|opposition|unsubscribe|do_?not_?sell|suppress|retirar\w*consentimiento"]),
    },
]

# --- soft-delete vs hard-delete ---------------------------------------------
_SOFT_DELETE_RE = compile_alt([
    r"deleted_?at|\bdeleted_at\b", r"is_?deleted", r"isDeleted", r"archived",
    r"soft_?delete", r"softdelete", r"SoftDeletes", r"paranoia", r"@SQLDelete",
    r"trashed", r"deletedAt", r"status\s*=\s*[\"']deleted", r"active\s*=\s*False",
    r"row_?status", r"deleted\s*=\s*True",
])
_HARD_DELETE_RE = compile_alt([
    r"DELETE\s+FROM", r"\.delete\(\)", r"\bdelete\b", r"\berase\b", r"\bremove\b",
    r"hard_?delete", r"purge", r"\bdestroy\b", r"TRUNCATE", r"DROP\s+TABLE",
    r"unlink\(|unset\b.*(?:field|attribute)",
])
_BACKUP_CASCADE_RE = compile_alt([
    r"backup", r"pg_dump", r"snapshot", r"replicat", r"read_?replica",
    r"elasticsearch|search_?index|opensearch|\bes_index|servicio.*indice",
    r"\bcache\b|\bredis\b", r"\bcdn\b", r"cloudfront", r"mirror",
    r"cold\s?storage", r"archive", r"blob|object\s?storage",
])


def scan(root: Path) -> list[Finding]:
    root = Path(root)
    obligaciones = load_obligaciones()
    hallazgos: list[Finding] = []

    # (archivo, linea) por derecho → presente
    found: dict[str, list[tuple[str, int]]] = {r["obligacion"]: [] for r in RIGHTS}
    found_strong: dict[str, list[tuple[str, int]]] = {r["obligacion"]: [] for r in RIGHTS}

    files = iter_source_files(root)
    for p in files:
        rel = abs_to_rel(root, p)
        previous = ""
        for lineno, line in enumerate(read_text(p).splitlines(), 1):
            ctx = f"{previous}\n{line}"  # decorador @app.get(...) + def ...
            for r in RIGHTS:
                if r["strong"].search(line) and _ROUTE_CTX_RE.search(ctx):
                    found_strong[r["obligacion"]].append((rel, lineno))
                if r["weak"].search(line):
                    # dedupe por derecho: guardamos el primero de cada archivo
                    if not any(a == rel for a, _ in found[r["obligacion"]]):
                        found[r["obligacion"]].append((rel, lineno))
            previous = line

    for r in RIGHTS:
        ob = r["obligacion"]
        if found_strong[ob]:
            for rel, ln in found_strong[ob][:1]:
                hallazgos.append(make_finding(
                    detector=DETECTOR, obligacion_id=ob,
                    archivo=rel, linea=ln,
                    evidencia=f"endpoint/servicio: {read_text(root / rel).splitlines()[ln-1].strip()[:150]}",
                    tipo="DETERMINISTA",
                    mensaje=(
                        f"se encontró mecanismo o ruta para el derecho de "
                        f"{r['nombre']} en {rel}:{ln}"
                    ),
                    prioridad_revision="MEDIA", confianza="alta",
                    obligaciones=obligaciones,
                ))
        elif found[ob]:
            rel, ln = found[ob][0]
            hallazgos.append(make_finding(
                detector=DETECTOR, obligacion_id=ob,
                archivo=rel, linea=ln,
                evidencia=f"mención: {read_text(root / rel).splitlines()[ln-1].strip()[:150]}",
                tipo="DETERMINISTA",
                mensaje=(
                    f"se encontró mención (sin contexto de ruta/endpoint) para el "
                    f"derecho de {r['nombre']} en {rel}:{ln}"
                ),
                prioridad_revision="BAJA", confianza="baja",
                obligaciones=obligaciones,
            ))
        else:
            hallazgos.append(make_finding(
                detector=DETECTOR, obligacion_id=ob,
                archivo=".", linea=0,
                evidencia="(ausencia) sin coincidencias para los patrones del derecho",
                tipo="DETERMINISTA",
                mensaje=(
                    f"no se ha encontrado ningún mecanismo, endpoint ni mención para "
                    f"el derecho de {r['nombre']} en el repositorio"
                ),
                prioridad_revision="ALTA", confianza="alta",
                obligaciones=obligaciones,
            ))

    # --- soft-delete vs hard-delete (Art. 17) --------------------------------
    soft_hits: list[tuple[str, int, str]] = []
    hard_hits: list[tuple[str, int, str]] = []
    for p in files:
        rel = abs_to_rel(root, p)
        for lineno, line in enumerate(read_text(p).splitlines(), 1):
            if _SOFT_DELETE_RE.search(line):
                soft_hits.append((rel, lineno, line.strip()[:150]))
            if _HARD_DELETE_RE.search(line):
                hard_hits.append((rel, lineno, line.strip()[:150]))

    if hard_hits:
        for rel, ln, ev in hard_hits[:1]:
            hallazgos.append(make_finding(
                detector=DETECTOR, obligacion_id="gdpr-art-17",
                archivo=rel, linea=ln,
                evidencia=ev,
                tipo="DETERMINISTA",
                mensaje=(
                    f"se encontró borrado directo/hard-delete en {rel}:{ln}; "
                    "el Art. 17 exige borrado real (no basta desindexación)"
                ),
                prioridad_revision="MEDIA", confianza="alta",
                obligaciones=obligaciones,
            ))
    if soft_hits:
        for rel, ln, ev in soft_hits[:1]:
            hallazgos.append(make_finding(
                detector=DETECTOR, obligacion_id="gdpr-art-17",
                archivo=rel, linea=ln,
                evidencia=ev,
                tipo="DETERMINISTA",
                mensaje=(
                    f"el borrado se implementa por soft-delete (`{ev.split()[0]}`) "
                    f"en {rel}:{ln}; un timestamp de eliminación no es borrado real "
                    "(Art. 17: 'erasure') y no propaga a backups/índices/terceros por sí solo"
                ),
                prioridad_revision="ALTA", confianza="alta",
                obligaciones=obligaciones,
            ))

    # propagación del borrado a backups/cache/índices (Art. 17(2))
    if hard_hits or soft_hits:
        backup_hits = [p for p in files if _BACKUP_CASCADE_RE.search(read_text(p)) and
                       any(part not in ("__pycache__", ".git") for part in p.parts)]
        if not backup_hits:
            hallazgos.append(make_finding(
                detector=DETECTOR, obligacion_id="gdpr-art-17",
                archivo=".", linea=0,
                evidencia="(ausencia) no se encontró referencia a backups/cachés/índices/terceros",
                tipo="DETERMINISTA",
                mensaje=(
                    "se encontró mecanismo de borrado pero no se ha encontrado referencia "
                    "a su propagación a backups, cachés, índices ni terceros (Art. 17(2))"
                ),
                prioridad_revision="MEDIA", confianza="baja",
                obligaciones=obligaciones,
            ))

    return hallazgos


def main(argv: list[str]) -> int:
    return run_detector_cli(sys.modules[__name__], argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
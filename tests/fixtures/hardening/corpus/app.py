# ATENCION — para quien mantenga este corpus (regresion de falsos positivos):
# Los detectores escanean el archivo COMPLETO: comentarios y docstrings son
# parte del input. No agregues aqui las palabras-faro que los detectores
# buscan (voz-a-texto, campos de minoridad, avisos/banderas de galletas del
# sitio), ni siquiera dentro de un comentario: se contarian como hallazgo y
# este corpus dejaria de ser el negativo limpio de test_corpus_no_false_alta.
# Ya hubo falsos positivos por docstrings que parecian inocentes. Para listar
# los tokens exactos que los detectores buscan, mira los patrones *_RE de
# cada detector en skills/legal-audit/scripts/detectors/ antes de editar.
"""Registrador de eventos de ejemplo para regresiones de contenido.

Este archivo define un campo con la forma ``lastTimestamp`` y una variable
``timestamp`` solo como codigo de ejemplo, sin describir ningun flujo
de datos de personas.
"""

import time


def record_event(event: str) -> dict:
    lastTimestamp = time.time()  # noqa: N806
    timestamp = lastTimestamp
    return {
        "event": event,
        "lastTimestamp": lastTimestamp,
        "timestamp": timestamp,
    }
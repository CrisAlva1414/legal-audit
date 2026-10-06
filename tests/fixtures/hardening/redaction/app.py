"""Fixture para el test de redacción (D11).

La línea 14 de `track()` contiene un valor con forma de secreto
(`api_key=sk-secretvalue123`). pii_in_logs emite un hallazgo y el valor debe
salir como [REDACTED] conservando la clave y el número de línea.
"""

import logging

logger = logging.getLogger("app")


def track(user):
    logger.info("user api_key=sk-secretvalue123 leaked to log")
    return user.id
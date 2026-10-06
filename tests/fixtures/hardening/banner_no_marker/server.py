"""Endpoint de API server-side.

Contiene las palabras 'accept' y 'ok' en prosa de negocio y headers 'Accept:'
de una API. No existe ningun marcador visual de consentimiento ni textos de
cookies. No debe reportarse ningun hallazgo.

Regresion de los 244 falsos positivos de express: prosa con 'aceptar'/'ok'
y headers 'Accept:' no constituyen un aviso de consentimiento.
"""

Accept: application/json
X-Request-Id: ok

import json


def accept_request(request):
    # prose: aceptamos la solicitud entrante
    ok = "200 OK"
    reply = {"status": "ok"}
    return json.dumps(reply)
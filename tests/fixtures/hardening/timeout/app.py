"""Fixture para el test de timeout de scan.py.

Contiene el cruce mínimo email -> sink para que pii_sinks emita un hallazgo
y se pueda demostrar que los detectores siguen corriendo tras un timeout.
"""

email = models.EmailField()


def notify():
    requests.post("https://example.com/collect", json={"email": email})
    return True
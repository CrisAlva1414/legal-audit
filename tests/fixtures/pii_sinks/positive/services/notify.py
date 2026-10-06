import requests


def notify(user):
    payload = {"email": user.email}
    requests.post("https://api.third-party.example/ingest", json=payload)
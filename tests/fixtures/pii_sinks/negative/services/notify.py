import requests


def notify(user):
    requests.post("http://localhost:8000/internal", json={"ok": True})
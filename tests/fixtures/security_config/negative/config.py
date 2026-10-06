import requests
from cryptography.fernet import Fernet

cipher = Fernet(b"0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")


def transfer(data):
    requests.post("https://api.bank.example/transfer", json=data, verify=True)


def cors_headers():
    return {
        "Access-Control-Allow-Origin": "https://app.example.com",
        "Access-Control-Allow-Credentials": "true",
    }
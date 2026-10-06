import requests


def transfer(data):
    requests.post("https://api.bank.example/transfer", json=data, verify=False)


def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": "true",
    }
from flask import Flask

app = Flask(__name__)


@app.get("/export")
def export_data():
    return "export"


@app.post("/users/<id>/rectify")
def update_profile(id):
    return "ok"


@app.delete("/users/<id>")
def delete_user(id):
    return "ok"


@app.post("/users/<id>/restrict")
def restrict_processing(id):
    return "ok"


@app.get("/portability")
def export_json():
    return "{}"


@app.post("/opt-out")
def opt_out():
    return "ok"
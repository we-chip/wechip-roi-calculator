from flask import Flask, send_from_directory
import os

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))


@app.route("/")
def index():
    return send_from_directory(BASE, "WECHIP_Configurateur_Client.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(BASE, filename)

from flask import Flask, send_from_directory, abort
import os

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))

# Explicit allowlist — the previous catch-all route exposed the entire repo
# (app.py, CLAUDE.md, shared/, docs/…). Only client-facing assets are served.
ALLOWED_FILES = {
    "WECHIP_Configurateur_Client.html",
    "wechip-tokens.css",
    "favicon.ico",
}
ALLOWED_DIR_PREFIXES = ("assets/", "fonts/")


@app.route("/")
def index():
    return send_from_directory(BASE, "WECHIP_Configurateur_Client.html")


@app.route("/<path:filename>")
def static_files(filename):
    if filename in ALLOWED_FILES or filename.startswith(ALLOWED_DIR_PREFIXES):
        return send_from_directory(BASE, filename)
    abort(404)


@app.after_request
def add_security_headers(resp):
    # Inline <style> and <script> are used in the calculator HTML, so CSP must
    # allow 'unsafe-inline' for those — still locks down all external sources.
    resp.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'",
    )
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return resp


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5051)), debug=False)

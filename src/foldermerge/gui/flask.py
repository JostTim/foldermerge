from flask import Flask, url_for, redirect, send_from_directory, abort

# from flask.sessions import SecureCookieSessionInterface
from os import urandom
from datetime import timedelta
from pathlib import Path
from foldermerge.core import HashLibrary
from webbrowser import open_new as open_new_webbrowser
from threading import Timer
from logging import basicConfig, StreamHandler

from .api import api_blueprint

LOGGING_LEVEL = "DEBUG"

base_dir = Path(__file__).parent

app = Flask(
    "FolderMerge",
    template_folder=base_dir / "templates",
    static_folder=base_dir / "static",
)
app.secret_key = urandom(24)  # or a static, secure key for production
app.permanent_session_lifetime = timedelta(minutes=30)

app.register_blueprint(api_blueprint, url_prefix="/api")


@app.route("/")
def serve_vue_app():
    if app.static_folder is None:
        return abort(404)
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def serve_static_files(path):
    if app.static_folder is None:
        return abort(404)

    try:
        # Try to serve the requested file from the static folder
        return send_from_directory(app.static_folder, path)
    except Exception as e:
        # If the file is not found, serve the index.html for Vue.js routing
        return redirect(url_for("serve_vue_app"))


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(str(base_dir / "static"), "favicon.svg", mimetype="image/svg+xml")


def run(host="127.0.0.1", port=5000):
    def open_browser():
        open_new_webbrowser(f"http://{host}:{port}/")

    # logging basic config
    basicConfig(level=LOGGING_LEVEL, handlers=[StreamHandler()])

    HashLibrary().set_cached_data()

    # open a simple thread that will open a browser window after 0.1s delay.
    # This will trigger while the http backend will have already started as "app.run" is a blocking statement.
    Timer(0.1, open_browser).start()

    # instanciate an HashLibrary at least once to be able to acesss it via cache afterwards
    app.run(host=host, port=port, debug=False)

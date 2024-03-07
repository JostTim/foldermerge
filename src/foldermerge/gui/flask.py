from flask import Flask, render_template, request, session, make_response, flash, url_for, redirect
from json import loads as json_loads
from os import urandom
from datetime import timedelta
from pathlib import Path
from foldermerge.core import FolderMerger
from webbrowser import open_new as open_new_webbrowser
from threading import Timer
from pandas import DataFrame

base_dir = Path(__file__).parent

app = Flask("FolderMerge", template_folder=base_dir /
            "templates", static_folder=base_dir / "static")

app.secret_key = urandom(24)  # or a static, secure key for production
app.permanent_session_lifetime = timedelta(minutes=5)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/view_results", methods=["POST"])
def view_report():
    try:
        reference_folder = Path(request.form["reference_folder"])
        compared_folders = request.form.get("compared_folders", "")
        compared_folders = compared_folders.split("*")
        refresh = json_loads(request.form.get("refresh", "false"))

        print(reference_folder)
        print(compared_folders)
        print(refresh)

        fm = FolderMerger(reference_folder, compared_folders,
                          refresh=refresh)  # type: ignore
        session.permanent = True
        session["reference_folder"] = str(reference_folder)
        session["compared_folders"] = [
            str(folder) for folder in compared_folders]

        report = fm.report(mode="dict")
        print(report)

        return render_template("report_view.html", report=report)
    except Exception as e:
        flash(f"{e} Error occurred. Please try again", "error")
        return redirect(url_for("index"))


@app.route("/view_inexistant_files", methods=["POST"])
def view_inexistant_files():
    reference_folder = session.get("reference_folder", None)
    compared_folders = session.get("compared_folders", [])

    if reference_folder is None:
        return redirect(url_for("index"))

    fm = FolderMerger(reference_folder, compared_folders,
                      refresh=False)  # type: ignore

    if fm is None:
        response = make_response(
            "FolderMerger data not found in the session", 404)
        return response

    df = fm.folders.child(
        0).comparisons[fm.folders.main.name].get_inexistant_files()

    return render_template("files_view_script.js", tree_html=render_tree(get_tree(df)))


def get_tree(data: DataFrame) -> dict:
    tree = {}
    for _, row in data.iterrows():
        parts = row["reldirpath"].split("\\")
        current_level = tree
        for part in parts:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
        current_level[row["name"]] = {
            "fullpath": row["path"], "hash": row["hash"], "uuid": row.name}
    return tree


def render_tree(tree: dict):
    html = ""
    for folder, contents in tree.items():
        if isinstance(contents, dict):
            if "fullpath" in contents.keys():
                # Handle the case where contents is dictionary representing a file
                html += '<table class="file-content">'
                for key, value in contents.items():
                    html += (
                        "<tr>"
                        f'<td class="category_key">{key}</td>'
                        "<td> : </td>"
                        f'<td class="category_value">{value}</td>'
                        "</tr>"
                    )
                html += "</table>"
            else:
                # contents is a dictionary (subfolder)
                html += f'<li class="folder">{folder}</li>'
                html += '<ul class="folder-content">'
                # Recursively render subdirectories
                html += render_tree(contents)
                html += "</ul>"
        else:
            continue
    return html


def run(host="127.0.0.1", port=5000):
    def open_browser():
        open_new_webbrowser(f"http://{host}:{port}/")

    Timer(1, open_browser).start()
    app.run(host=host, port=port, debug=False)

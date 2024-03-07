from flask import Flask, render_template, request, session, make_response, flash, url_for, redirect
from json import loads as json_loads
from os import urandom
from datetime import timedelta
from pathlib import Path
from foldermerge.core import FolderMerger, FolderChecker, FolderComparator
from webbrowser import open_new as open_new_webbrowser
from threading import Timer
from pandas import DataFrame
from traceback import format_exc

base_dir = Path(__file__).parent

app = Flask("FolderMerge", template_folder=base_dir / "templates", static_folder=base_dir / "static")

app.secret_key = urandom(24)  # or a static, secure key for production
app.permanent_session_lifetime = timedelta(minutes=5)


@app.route("/")
def index():
    reference_folder = session.get("reference_folder", None)
    compared_folders = session.get("compared_folders", [])
    return render_template(
        "index.html",
        compared_folders=compared_folders,
        reference_folder=reference_folder,
    )


@app.route("/view_results", methods=["POST"])
def view_report():
    if not request.form["reference_folder"]:
        flash("A reference folder wasn't selected. Please select one.", "error")
        return redirect(url_for("index"))

    try:
        reference_folder = Path(request.form["reference_folder"])
        compared_folders = request.form.get("compared_folders", "")
        compared_folders = compared_folders.split("*")
        refresh = json_loads(request.form.get("refresh", "false"))

        print(reference_folder)
        print(compared_folders)
        print(refresh)

        fm = FolderMerger(reference_folder, compared_folders, refresh=refresh)  # type: ignore
        session.permanent = True
        session["reference_folder"] = str(reference_folder)
        session["compared_folders"] = [str(folder) for folder in compared_folders]

        reference_report = fm.folders.main.report(mode="dict")
        report = fm.report(mode="dict")
        print(report)

        categories_legend = {
            "total_files": {"description": "All files found", "selection": "all"},
            "identical_content": {
                "description": "Files exiting in reference (name & content matches)",
                "selection": "identical",
            },
            "inexistant_content": {"description": "Files inexistant in reference", "selection": "inexistant"},
            "moved_contents": {"description": "Moved files (content matches)", "selection": "moved"},
            "changed_contents": {"description": "Modified content files (name matches)", "selection": "changed"},
        }

        return render_template(
            "report_view.html", report=report, reference_report=reference_report, categories_legend=categories_legend
        )
    except Exception as e:
        tb = format_exc()
        print(tb)

        flash(f"{e} Error occurred. Please try again", "error")
        # return redirect(url_for("index"))
        return render_template("index.html")


@app.route("/view_files", methods=["POST"])
def view_files():
    reference_folder = session.get("reference_folder", None)
    compared_folders = session.get("compared_folders", [])

    folder_selection = request.form["folder_selection"]
    files_selection = request.form["files_selection"]
    print(folder_selection)
    print(files_selection)

    if reference_folder is None:
        flash("A reference folder wasn't selected. Please select one.", "error")
        return redirect(url_for("index"))

    fm = FolderMerger(reference_folder, compared_folders, refresh=False)

    folder = fm.folders[folder_selection]

    if folder.is_reference:  # type: ignore
        df = folder.data  # type: ignore
        reference_folder = None
    else:
        df = folder.comparisons[fm.folders.main.name].get_files(files_selection)  # type: ignore

    return render_template(
        "files_view.html",
        tree_html=render_tree(get_tree(df)),
        current_folder=folder.repo_path,  # type:ignore
        reference_folder=reference_folder,
        selection=files_selection,
    )


def get_tree(data: DataFrame) -> dict:
    tree = {}
    for _, row in data.iterrows():
        parts = row["reldirpath"].split("\\")
        current_level = tree
        for part in parts:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
        current_level[row["name"]] = {"fullpath": row["fullpath"], "hash": row["hash"], "uuid": row.name}
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

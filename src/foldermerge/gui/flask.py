from flask import Flask, render_template, request, session, flash, url_for, redirect, send_from_directory

# from flask.sessions import SecureCookieSessionInterface
from json import loads as json_loads
from os import urandom
from datetime import timedelta
from pathlib import Path
from foldermerge.core import FolderMerger, HashLibrary
from webbrowser import open_new as open_new_webbrowser
from threading import Timer
from pandas import DataFrame
from traceback import format_exc
from logging import basicConfig, StreamHandler, getLogger

LOGGING_LEVEL = "DEBUG"

base_dir = Path(__file__).parent

app = Flask("FolderMerge", template_folder=base_dir /
            "templates", static_folder=base_dir / "static")

app.secret_key = urandom(24)  # or a static, secure key for production
app.permanent_session_lifetime = timedelta(minutes=30)


@app.route("/")
def index():
    return render_template("files_selection.html")

    # @app.route("/")
    # def index():
    #     logger = getLogger("gui.index")
    #     logger.info("Connexion at homepage")
    #     reference_folder = session.get("reference_folder", None)
    #     compared_folders = session.get("compared_folders", [])
    #     return render_template(
    #         "index.html",
    #         compared_folders=compared_folders,
    #         reference_folder=reference_folder,
    #     )


@app.route("/view_results", methods=["POST"])
def view_report():
    if not request.form["reference_folder"]:
        flash("A reference folder wasn't selected. Please select one.", "error")
        return redirect(url_for("index"))

    try:
        reference_folder = Path(request.form["reference_folder"])
        _compared_folders = request.form.get("compared_folders", "")
        _compared_rel_roots = request.form.get("compared_rel_roots", "")

        compared_folders = []
        search_paths = []
        for comp, root in zip(_compared_folders.split("*"), _compared_rel_roots.split("*")):
            if comp == "" or comp is None:
                continue

            if root == "":
                root = comp

            if len(comp) >= len(root):
                # if comp is longer than root, the search path is comp, not root. So we swap
                compared_folders.append(root)
                search_paths.append(comp)
            else:
                compared_folders.append(comp)
                search_paths.append(root)

        refresh = json_loads(request.form.get("refresh", "false"))

        print("reference_folder: ", reference_folder)
        print("compared_folders: ", compared_folders)
        print("search_paths: ", search_paths)
        print("refresh: ", refresh)

        fm = FolderMerger(
            destination_repo=reference_folder,
            sources_repo=compared_folders,
            search_paths_repo=search_paths,
            refresh=refresh,
        )  # type: ignore

        session.permanent = True
        session["reference_folder"] = str(reference_folder)
        session["compared_folders"] = [
            str(folder) for folder in compared_folders]
        session["search_paths"] = [str(folder) for folder in search_paths]

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


def get_session():
    reference_folder = session.get("reference_folder", None)
    compared_folders = session.get("compared_folders", [])
    search_paths = session.get("search_paths", [])

    try:
        if reference_folder is None:
            raise ValueError("reference_folder cannot be None")
        fm = FolderMerger(
            destination_repo=reference_folder,
            sources_repo=compared_folders,
            search_paths_repo=search_paths,
            refresh=False,
        )
        return fm
    except Exception:
        return None


def set_session(foldermerger: FolderMerger):
    session.permanent = True
    session["reference_folder"] = foldermerger.reference_folder_path
    session["compared_folders"] = foldermerger.compared_folders_paths
    session["search_paths"] = foldermerger.search_paths


@app.route("/view_files", methods=["POST"])
def view_files():

    selection_map = {
        "identical": ["name", "content"],
        "inexistant": [],
        "moved": ["content"],
        "changed": ["name"],
        "all": ["name", "content"],
    }

    fm = get_session()

    if fm is None:
        flash("A reference folder wasn't selected. Please select one.", "error")
        return redirect(url_for("index"))

    folder_selection = request.form["folder_selection"]
    files_selection = request.form["files_selection"]
    print(folder_selection)
    print(files_selection)

    folder = fm.folders[folder_selection]

    if folder.is_reference:  # type: ignore
        df = folder.data  # type: ignore
        reference_folder = None
    else:
        df = folder.comparisons[fm.folders.main.name].get_files(
            files_selection)  # type: ignore

    return render_template(
        "files_view.html",
        tree_html=render_tree(get_tree(df, selection_map[files_selection])),
        current_folder=folder.repo_path,  # type:ignore
        reference_folder=reference_folder,
        selection=files_selection,
    )


@app.route("/file_hint", methods=["POST"])
def file_hint():
    data = request.get_json()
    uuids = json_loads(data.get("uuids", "[]"))
    hash_library = HashLibrary(cached=True)
    html_content = ""
    for uuid in uuids:
        file = hash_library.data.loc[uuid].to_dict()
        html_content += render_file(file, add_info_button=False)
    return html_content


"""
## The nex front shall : 
- Have a top ribbon sticky, 
    - leads back to home (folders selection)
    - leads back to previous step (breadcrumbs) like report view, wich shows repos summarized results, repo edition selection

"""


@app.route("/file_action", methods=["POST"])
def file_action():
    data = request.get_json()
    uuids = json_loads(data.get("uuids", "[]"))
    hash_library = HashLibrary(cached=True)
    html_content = ""
    for uuid in uuids:
        file = hash_library.data.loc[uuid].to_dict()
        html_content += render_file(file, add_info_button=False)
    return html_content


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(str(base_dir / "static"), "favicon.svg", mimetype="image/svg+xml")


def get_tree(data: DataFrame, match_types=[]) -> dict:
    if not isinstance(match_types, list):
        match_types = [match_types]
    print(match_types)

    tree = {}
    for _, row in data.iterrows():
        parts = row["reldirpath"].split("\\")
        current_level = tree
        for part in parts:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
        matches = []
        for match_type in match_types:
            # type: ignore
            matches.extend(row.get(f"{match_type}_matches", []))
        matches = list(set(matches))
        current_level[row["name"]] = {
            "fullpath": row["fullpath"],
            "filename": row["filename"],
            "hash": row["hash"],
            "uuid": row.name,
            "matches": matches,
        }
    return tree


def render_tree(tree: dict) -> str:
    html = ""
    for folder, contents in tree.items():
        if isinstance(contents, dict):
            if "fullpath" in contents.keys():
                # contents is a file
                html += render_file(contents)
            else:
                # contents is a subfolder
                html += f'<li class="folder">{folder}</li>'
                html += '<ul class="folder-content">'
                # Recursively render subdirectories
                html += render_tree(contents)
                html += "</ul>"
        else:
            continue
    return html


def render_file(file: dict, add_info_button=True) -> str:
    html = '<div class = "file-container"><table class="file-content hint-target"'
    file_matches = file.get("matches", [])
    file_uuid = file.get("uuid", None)
    if len(file_matches):
        html += f' data-matches-uuids="{file_matches}">'
    else:
        html += ">"
    html += "<tbody>"
    for row_num, (key, value) in enumerate(file.items()):
        # if row_num == 1 and add_info_button:
        #     html += '<tr><td colspan="2"><div class="toggle-info-button">▶</div></td></tr>'
        if key == "matches":
            value = len(value)
        html += '<tr class="additional-info">'
        html += f'<td><div class="category_key category_{key}">{key}</div></td>'
        html += f'<td><div class="category_value category_{key}" onclick="copyToClipboard(this)">{value}</div></td>'
        if key == "fullpath":
            html += '<td><span class="material-symbols-outlined">content_copy</span></td>'

        html += "</tr>"

    html += "</tbody></table>"
    if file_uuid is not None:
        html += f'<div class="action-button" id="{file_uuid}_copier">Copy file to reference</div>'
        html += f'<div class="action-button" id="{file_uuid}_deleter">Delete file</div>'
    html += "</div>"
    return html


def run(host="127.0.0.1", port=5000):
    def open_browser():
        open_new_webbrowser(f"http://{host}:{port}/")

    # logging basic config
    basicConfig(level="DEBUG", handlers=[StreamHandler()])

    HashLibrary().set_cached_data()

    # open a simple thread that will open a browser window after 1s delay.
    # This will trigger while the http backend will have already started as "app.run" is a blocking statement.
    Timer(1, open_browser).start()

    # instanciate an HashLibrary at least once to be able to acesss it via cache afterwards
    app.run(host=host, port=port, debug=False)


# tqdm_capturing_regexp = r"\| (?P<current>\d+)\/(?P<total>\d+) \[(?P<t_elapsed>[\d:-]+)<(?P<t_remaining>[\d:-]+),"

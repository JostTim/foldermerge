from flask import (
    Blueprint,
    render_template,
    request,
    session,
    flash,
    url_for,
    redirect,
    send_from_directory,
    jsonify,
    abort,
)


# from flask.sessions import SecureCookieSessionInterface
from json import loads as json_loads
from pathlib import Path
from foldermerge.core import FolderMerger, HashLibrary
from webbrowser import open_new as open_new_webbrowser
from pandas import DataFrame
from traceback import format_exc
from logging import getLogger

from flask_restful import Resource, Api, reqparse

api_blueprint = Blueprint("api", __name__)

api = Api(api_blueprint)


class ApiRoot(Resource):
    def get(self):
        return {"message": "This is the root of the API routes"}


class ApiData(Resource):
    def get(self):
        return FILES_DATA


class ApiError(Resource):
    def get(self, path):
        return {"error": f"The api endpoint {path} do not exist !"}


FILES_DATA = {
    "name": "C:/",
    "files": [
        {"key": "sCABOON.pu", "value": "thing/foust/sCABOON.pu", "file_uuid": "zdaz", "file_matches": ["187165"]},
        {"key": "lattix.isi", "value": "thing/testounet/blabla/lattix.isi", "file_uuid": "187165", "file_matches": []},
    ],
    "folders": [
        {
            "name": "subfolder",
            "files": [
                {
                    "key": "sCABOON.pu",
                    "value": "thing/foust/sCABOON.pu",
                    "file_uuid": "zdaz",
                    "file_matches": ["187165"],
                }
            ],
            "folders": [],
        }
    ],
}


api.add_resource(ApiRoot, "/")
api.add_resource(ApiData, "/data")
api.add_resource(ApiError, "/<string:path>")

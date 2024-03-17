from .core import FolderMerger, clear_results
from . import custom_accessors as _
import logging, argparse, sys

logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(" %(levelname)-8s : %(message)s")
handler.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def console():
    parser = argparse.ArgumentParser(
        prog="foldermerge", description="Performs folder structure scan and difference to help in your cleaning process"
    )
    parser.add_argument("reference_folder", nargs="?", default=None, help="Path to the reference folder")
    parser.add_argument(
        "compared_folders", nargs="*", default=[], help="Paths to folders to be compared with the reference folder"
    )
    parser.add_argument(
        "--gui",
        "-g",
        action="store_true",
        help="Launches the graphical interface mode of foldermerge, in a browser tab",
    )
    parser.add_argument("--port", help="Port in case of GUI run", default="5000")
    parser.add_argument("--host", help="Host IP in case of GUI run", default=None)

    args = parser.parse_args()
    if args.gui:
        from .gui.flask import run as run_gui

        if args.host is None:
            host = "127.0.0.1"
        else:
            host = args.host
        run_gui(host, args.port)
        return

    if args.reference_folder is None:
        raise ValueError("You must supply at least one reference folder path as first argument")
    logger.info(f"Selected reference folder is {args.reference_folder}")
    fm = FolderMerger(args.reference_folder, args.compared_folders)
    logger.info(fm.report())


def create_app():
    from .gui.flask import app

    return app


if __name__ == "__main__":
    console()

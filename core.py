import os
from pathlib import Path
import pandas as pd
import hashlib
from tqdm import tqdm

tqdm.pandas()

SAVE_FOLDER = str(Path.home() / "Downloads" / "FILE_HASHES")


def deep_hash(values):
    try:
        return hash(values)
    except TypeError:
        if isinstance(values, tuple):
            print(values)
            return hash(values)
        elif isinstance(values, list):
            return hash(tuple(values))
        hashes = []
        for item in values.values():
            hashes.append(deep_hash(item))
        return deep_hash(hashes)


def get_save_name(repo_path: str) -> str:
    os.makedirs(SAVE_FOLDER, exist_ok=True)
    sha1 = hashlib.sha1()
    sha1.update(repo_path.encode())
    return sha1.hexdigest()[0:8]


def get_save_path(repo_path: str) -> str:
    return os.path.join(SAVE_FOLDER, f"{get_save_name(repo_path)}.pickle")


def save_repo(repo_path: str, data: pd.DataFrame):
    if data is None:
        return False
    data.to_pickle(get_save_path(repo_path))
    return True


def load_repo(repo_path: str):
    save_path = get_save_path(repo_path)
    if os.path.isfile(save_path):
        return pd.read_pickle(save_path)
    return None


class FolderMerger:

    def __init__(self, main_repo: str, duplicates_repo: list = []):

        self.main_repo_path = main_repo
        self.main_struct = self.get_struct(self.main_repo_path)

        self.child_structs = {}
        for repo_path in duplicates_repo:
            self.child_structs[repo_path] = self.get_struct(repo_path)

        for repo_path in self.child_structs.keys():
            self.child_structs[repo_path] = self.compare_to_main(self.child_structs[repo_path])

        self.save()

    def save(self):
        save_repo(self.main_repo_path, self.main_struct)
        for repo_path in self.child_structs.keys():
            save_repo(repo_path, self.child_structs[repo_path])

    def get_struct(self, repo_path: str):
        data = load_repo(repo_path)
        if data is None:
            data = self.gather_files(repo_path)
            data = self.gather_hashes(data)
        return data

    def gather_files(self, repo_path: str) -> pd.DataFrame:

        structure = []
        for root, dirs, files in tqdm(os.walk(repo_path), desc="Finding all files in the repo"):
            if not files:
                continue

            relative_dir = os.path.relpath(root, repo_path)
            dirs = relative_dir.split(os.sep)
            dirs = [] if dirs == ["."] else dirs

            for file in files:
                file_fullpath = os.path.join(root, file)
                file_relpath = os.path.join(relative_dir, file)
                name, ext = os.path.splitext(file)
                ctime = os.path.getctime(file_fullpath)
                mtime = os.path.getmtime(file_fullpath)
                time = ctime if ctime > mtime else mtime
                file_record = {
                    "filename": file,
                    "name": name,
                    "ext": ext,
                    "fullpath": file_fullpath,
                    "relpath": file_relpath,
                    "dirs": dirs,
                    "ctime": ctime,
                    "mtime": mtime,
                    "time": time
                }

                file_record["uuid"] = deep_hash(file_record)
                structure.append(file_record)

        return pd.DataFrame(structure).set_index("uuid")

    def compare_to_main(self, repo_struct: pd.DataFrame):
        repo_struct["content_matches"] = [[]] * len(repo_struct)
        repo_struct["name_matches"] = [[]] * len(repo_struct)
        for index, row in tqdm(repo_struct.iterrows(), total=len(repo_struct), desc="comparing to main"):
            matches = self.main_struct.relpath == row.relpath
            matches = matches[matches]
            if len(matches):
                repo_struct.at[index, "name_matches"] = matches.index.tolist()

            matches = self.main_struct.hash == row.hash
            matches = matches[matches]
            if len(matches):
                repo_struct.at[index, "content_matches"] = matches.index.tolist()

        return repo_struct

    def gather_hashes(self, repo_struct: pd.DataFrame):
        repo_struct["hash"] = repo_struct.fullpath.progress_apply(self.get_hash)
        return repo_struct

    def get_hash(self, path: str):

        BUF_SIZE = 65536
        sha1 = hashlib.sha1()
        with open(path, "rb") as f:
            while True:
                content = f.read(BUF_SIZE)
                if not content:
                    break
                sha1.update(content)
        return sha1.hexdigest()

    def __str__(self):
        supps = "\n".join(
            [
                f"{repo_path} : {get_save_name(self.main_repo_path)}" for repo_path in self.child_structs.keys()
            ]
        )
        supps = f" - {supps}" if supps else ""
        return f"<GatherHashes with main : {get_save_name(self.main_repo_path)}{supps}>"


if __name__ == "__main__":
    data = FolderMerger(r"C:\Users\Timothe\NasgoyaveOC\Projets", [r"C:\Users\Timothe\NasgoyaveOC\Projets"])
    print(data)
    print(data.main_struct)
    print(len(data.main_struct))
    print(list(data.child_structs.values())[0])

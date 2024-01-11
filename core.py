import os
from pathlib import Path
import pandas as pd
import hashlib
from tqdm import tqdm
import json
import traceback

tqdm.pandas()


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


class StatusFile():

    def __init__(self):
        self.save_path = str(Path.home() / "Downloads" / "FILE_HASHES" / "status.json")
        self.make()

    def make(self):
        if not os.path.isfile(self.save_path):
            with open(self.save_path, "w") as f :
                json.dump({}, f)

    def read_all(self):
        with open(self.save_path, "r") as f :
            return json.load(f)

    def write(self, name, status):
        data = self.read_all()
        data.update({name: status})
        with open(self.save_path, "w") as f :
            json.dump(data, f)

    def read(self, name):
        return self.read_all().get(name, "not_started")


class FolderChecker:

    SAVE_FOLDER = str(Path.home() / "Downloads" / "FILE_HASHES")
    data = None
    structure = None

    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.name = self.get_save_name()
        self.save_path = self.get_save_path()

    def get_save_path(self) -> str:
        os.makedirs(self.SAVE_FOLDER, exist_ok=True)
        return os.path.join(self.SAVE_FOLDER, f"{self.name}.pickle")

    def get_save_name(self) -> str:
        sha1 = hashlib.sha1()
        sha1.update(self.repo_path.encode())
        return sha1.hexdigest()[0:8]

    def save(self):
        print(f"saving {self}")
        if self.data is None:
            return False
        self.data.to_pickle(self.save_path)
        return True

    def load(self):
        print(f"loading {self}")
        if os.path.isfile(self.save_path):
            self.data = pd.read_pickle(self.save_path)
            return
        self.data = None

    def gather_files(self):

        self.structure = []
        print(f"Finding all files in the repo {self.repo_path}")
        for root, dirs, files in tqdm(os.walk(self.repo_path), desc="Searching"):
            if not files:
                continue

            relative_dir = os.path.relpath(root, self.repo_path)
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
                self.structure.append(file_record)

        if len(self.structure) == 0 :
            raise IOError("Found no files !")
        else :
            self.data = pd.DataFrame(self.structure).set_index("uuid")

    def __enter__(self):
        return self

    def run(self):
        self.load()
        if StatusFile().read(self.name) == "success" :
            return
        if self.data is None :
            self.gather_files()
            self.gather_hashes()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            traceback_str = ''.join(traceback.format_exception(exc_type, exc_val, exc_tb))
            print("Traceback: ", traceback_str)

            if exc_type is IOError:
                StatusFile().write(self.name, "no_file_error")
                return True

            if self.data is None :
                StatusFile().write(self.name, "gather_error")
                if self.structure is None :
                    print(f"error {exc_val} for {self} with traceback {exc_tb}")
                    return True
                self.data = pd.DataFrame(self.structure).set_index("uuid")
            else :
                StatusFile().write(self.name, "hashes_error")
            self.save()
            return True  # do not propagate exception
        else :
            StatusFile().write(self.name, "success")
            self.save()

    def gather_hashes(self):
        self.data["hash"] = self.data.fullpath.progress_apply(self.get_hash)

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

    def compare(self, compare_struct: pd.DataFrame):
        self.data["content_matches"] = [[]] * len(self.data)
        self.data["name_matches"] = [[]] * len(self.data)
        for index, row in tqdm(self.data.iterrows(), total=len(self.data), desc="comparing to main"):
            matches = compare_struct.relpath == row.relpath
            matches = matches[matches]
            if len(matches):
                self.data.at[index, "name_matches"] = matches.index.tolist()

            matches = compare_struct.hash == row.hash
            matches = matches[matches]
            if len(matches):
                self.data.at[index, "content_matches"] = matches.index.tolist()

        return self.data

    def __str__(self):
        return f"<Folder with name-{self.name} and path : {self.repo_path}>"


class FolderMerger:

    def __init__(self, main_repo: str, duplicates_repo: list = []):

        self.structs = {}

        self.structs["main"] = FolderChecker(main_repo)
        for index, repo_path in enumerate(duplicates_repo):
            self.structs[f"child_{index}"] = FolderChecker(repo_path)

        for struct in self.structs.values():
            with struct :
                struct.run()

        for name, struct in self.structs.items():
            if name == "main":
                continue
            struct.compare(self.structs["main"])

    def __str__(self):
        supps = "\n".join([f"{struct}" for struct in self.structs])
        return f"<GatherHashes with folders :\n{supps}>"


if __name__ == "__main__":
    data = FolderMerger(r"C:\Users\Timothe\NasgoyaveOC\Projets", [r"C:\Users\Timothe\NasgoyaveOC\Projets"])
    print(data)
    print(data.main_struct)
    print(len(data.main_struct))
    print(list(data.child_structs.values())[0])

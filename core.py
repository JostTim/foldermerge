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

    def __init__(self, owner):
        self.save_path = str(Path.home() / "Downloads" / "FILE_HASHES" / "status.json")
        self.make()
        self.owner = owner

    def make(self):
        if not os.path.isfile(self.save_path):
            with open(self.save_path, "w") as f :
                json.dump({}, f)

    def read_all(self):
        with open(self.save_path, "r") as f :
            return json.load(f)

    def write(self, folder, status):
        data = self.read_all()

        if isinstance(self.owner, FolderChecker):
            catergory_key = "checks"
            object_key = "me"
        elif isinstance(self.owner, FolderComparator):
            catergory_key = "comparison"
            object_key = self.owner.name
        else :
            raise ValueError("must be FolderChecker or FolderComparator")

        # select and update with current obj dict, the key of the folder
        selection = data.get(self.owner.foldername, {})
        data.update({self.owner.foldername: selection})

        # select and update with current obj dict, the key of the action (check, compare)
        selection = selection.get(catergory_key, {})
        data[self.owner.foldername].update({catergory_key: selection})

        # select and update with current obj dict, the key of the action (check, compare)
        selection = selection.get(catergory_key, {})
        data[self.owner.foldername].update({catergory_key: selection})

        data.update({folder.name: {"status": status, "path" : folder.repo_path}})
        with open(self.save_path, "w", newline='\n') as f :
            json.dump(data, f, indent=4, sort_keys=True)

    def read(self, folder):
        return self.read_all().get(folder.name, {}).get("status", "not_started")


class FolderChecker:

    SAVE_FOLDER = str(Path.home() / "Downloads" / "FILE_HASHES")
    data = None
    structure = None
    error = "undefined"

    def __init__(self, repo_path:str, name:str=None):
        self.repo_path = repo_path
        self.name = self.get_save_name() if name is None else "calc_" + name
        self.foldername = self.name
        self.save_path = self.get_save_path()

        self.load()

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
        StatusFile().write(self, self.error)
        return True

    def load(self):
        print(f"loading {self}")
        if os.path.isfile(self.save_path):
            self.data = pd.read_pickle(self.save_path)
            return
        self.data = None

    def gather_files(self, mode=False):

        self.set_error("gather_error")

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
                if mode :
                    if file_fullpath in self.data.fullpath :
                        continue
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
            if mode :
                temp_data = pd.DataFrame(self.structure).set_index("uuid")
                self.data = pd.concat([self.data, temp_data]).drop_duplicates(subset=["fullpath"], keep="first")
            else :
                self.data = pd.DataFrame(self.structure).set_index("uuid")

    def __enter__(self):
        return self

    def run(self):
        if "success" not in self.get_error() and "comparison" not in self.get_error():
            mode = False if self.data is None else True
            self.gather_files(mode)
            self.gather_hashes(mode)

    def set_error(self, error_name):
        self.error = error_name

    def get_error(self):
        return StatusFile().read(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            print("Traceback: ", ''.join(traceback.format_exception(exc_type, exc_val, exc_tb)))

            if exc_type is IOError:
                self.set_error("no_file_error")
                return True

            if self.data is None :
                if self.structure is None :
                    print(f"error {exc_val} for {self} with traceback {exc_tb}")
                    return True
                self.data = pd.DataFrame(self.structure).set_index("uuid")

            self.save()
            return True  # do not propagate exception
        else :
            if "content_matches" in self.data.columns :
                self.set_error("comparison_success")
            else :
                self.set_error("run_success")

        self.save()

    def gather_hashes(self, mode=False):
        if mode :
            if "hash" in self.data.columns :
                sel = self.data.hash.isna()
                if len(sel[sel]):
                    for index, row in tqdm(self.data.iterrows()):
                        if row.hash is None :
                            self.data.at[index, "hash"] = self.get_hash(row.fullpath)
                return
        self.set_error("hashes_error")
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



    
    def __str__(self):
        return f"<Folder with name {self.name} and path : {self.repo_path}>"

    def get_diffs(self, column, equal=True):
        def isempty(cell):
            return bool(len(cell)) if equal else not bool(len(cell))

        selector = self.data[column].apply(isempty)
        return self.data[selector]

    def get_identical_files(self):

        identical_contents = self.get_diffs("content_matches", True)
        identical_names = self.get_diffs("name_matches", True)

        sel = identical_names.index.isin(identical_contents.index)
        return identical_names[sel]

    def get_inexistant_files(self):

        diff_contents = self.get_diffs("content_matches", False)
        diff_names = self.get_diffs("name_matches", False)

        sel = diff_names.index.isin(diff_contents.index)
        return diff_names[sel]

    def get_moved_files(self):

        identical_contents = self.get_diffs("content_matches", True)
        diff_names = self.get_diffs("name_matches", False)

        sel = diff_names.index.isin(identical_contents.index)
        return diff_names[sel]

    def get_changed_files(self):

        diff_contents = self.get_diffs("content_matches", False)
        identical_names = self.get_diffs("name_matches", True)

        sel = identical_names.index.isin(diff_contents.index)
        return identical_names[sel]


    def dates_results(self, result, match_column):

        def is_most_recent(row, reference):
            ref_ix = row.name_matches[0]
            ref_row = reference.loc[ref_ix]

            return (row.ctime > ref_row.ctime, row.mtime > ref_row.mtime, row.time > ref_row.time)

        def most_recent_no_ambiguity(cell):
            # returns True if all the metric are more recent in the child vs main. Otherwise, False
            return all(cell)

        def most_old_no_ambiguity(cell):
            # returns True if any of the metric is more recent in the child vs main. Otherwise False
            return not any(cell)

        result = result.copy()
        result["most_recent"] = result.apply(is_most_recent, reference=main, axis=1)


    def comparison_results(self):
        print(f"Report of contents for repo {self.name} at {self.repo_path}:")

        identical_contents = self.get_identical_files()
        inexistant_contents = self.get_inexistant_files()
        moved_contents = self.get_moved_files()
        changed_contents = self.get_changed_files()

        print(f" - {len(self.data)} total files found.\n"
              f" - {len(identical_contents)} identical files (will be deleted)\n"
              f" - {len(inexistant_contents)} inexistant files (will be copied in main)\n"
              f" - {len(moved_contents)} moved files (same content, different location) (tbd)\n"
              f" - {len(changed_contents)} changed files (same location, different content) (tbd)\n"
              )


class FolderComparator:

    SAVE_FOLDER = str(Path.home() / "Downloads" / "FILE_HASHES")
    data = None

    def __init__(self, current : FolderChecker, reference: FolderChecker):
        self.current = current
        self.reference = reference
        self.foldername = self.current.foldername

        self.name = self.current.name + "_vs_" + self.reference.name

        self.save_path = self.get_save_path()

    def get_save_path(self) -> str:
        os.makedirs(self.SAVE_FOLDER, exist_ok=True)
        return os.path.join(self.SAVE_FOLDER, f"{self.name}.pickle")

    def get_matches(self, cell, compared_data):
        matches = compared_data == cell
        matches = matches[matches]
        if len(matches):
            return matches.index.tolist()
        return []

    def compare(self, mode=False):
        self.set_error("comparison_error")

        if (self.get_error() != "comparison_success" and mode) or "name_matches" not in self.data.columns :
            print("Comparing names:")
            self.data["name_matches"] = self.data.relpath.progress_apply(
                self.get_comparison, compared_data=compare_struct.data.relpath)

        if (self.get_error() != "comparison_success" and mode) or "content_matches" not in self.data.columns :
            print("Comparing hashes:")
            self.data["content_matches"] = self.data.hash.progress_apply(
                self.get_comparison, compared_data=compare_struct.data.hash)


    def save(self):
        print(f"saving {self}")
        if self.data is None:
            return False
        self.data.to_pickle(self.save_path)
        StatusFile().write(self, self.error)
        return True

    def load(self):
        print(f"loading {self}")
        if os.path.isfile(self.save_path):
            self.data = pd.read_pickle(self.save_path)
            return
        self.data = None


class FolderMerger:

    def __init__(self, main_repo: str, duplicates_repo: list = [], skip_checks=False):

        self.structs = {}

        self.structs["main"] = FolderChecker(main_repo)
        for index, repo_path in enumerate(duplicates_repo):
            self.structs[f"child_{index}"] = FolderChecker(repo_path)

        if skip_checks :
            return

        for struct in self.structs.values():
            with struct :
                struct.run()

        for name, struct in self.structs.items():
            if name == "main":
                continue
            with struct :
                struct.compare(self.main, False)

    @property
    def main(self):
        return self.structs["main"]

    def __str__(self):
        supps = "\n".join([f"{struct}" for struct in self.structs])
        return f"<GatherHashes with folders :\n{supps}>"

    def get_child(self, child_name=None):
        if child_name is None :
            child_name = [struct.name for key, struct in self.structs.items() if key != "main"][0]
        elif isinstance(child_name, int): 
            child_name = [struct.name for key, struct in self.structs.items() if key != "main"][child_name]
        got = [child for name, child in self.structs.items() if child.name == child_name]
        if len(got):
            return got[0]
        else :
            raise ValueError(f"No child with name {child_name}")

    def report(self):
        for name, struct in self.structs.items():
            if name == "main":
                continue
            struct.comparison_results()


if __name__ == "__main__":
    data = FolderMerger(r"C:\Users\Timothe\NasgoyaveOC\Projets", [r"C:\Users\Timothe\NasgoyaveOC\Projets"])
    print(data)
    print(data.main_struct)
    print(len(data.main_struct))
    print(list(data.child_structs.values())[0])

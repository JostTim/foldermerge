from pathlib import Path
import pandas as pd
import hashlib
from tqdm import tqdm
import json
import traceback

tqdm.pandas()


def get_default_results_path():
    return Path.home() / "Downloads" / "FILE_HASHES"


RESULTS_PATH = get_default_results_path()


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


class StatusFile:
    def __init__(self, owner):
        self.save_path = Path(RESULTS_PATH) / "status.json"
        self.makefile()
        self.owner = owner

    def makefile(self):
        if not self.save_path.is_file():
            with open(self.save_path, "w") as f:
                json.dump({}, f)

    def read_all(self):
        with open(self.save_path, "r") as f:
            return json.load(f)

    def select_data(self, data):
        if isinstance(self.owner, FolderChecker):
            catergory_key = "checks"
        elif isinstance(self.owner, FolderComparator):
            catergory_key = "comparison"
        else:
            raise ValueError("must be FolderChecker or FolderComparator")

        selection = data.get(self.owner.foldername, {})
        data.update({self.owner.foldername: selection})

        # select and update with current obj dict, the key of the action (check, compare)
        selection = selection.get(catergory_key, {})
        data[self.owner.foldername].update({catergory_key: selection})

        return selection

    def write(self, status):
        data = self.read_all()

        selection = self.select_data(data)

        if isinstance(self.owner, FolderChecker):
            content = {"status": status, "path": self.owner.repo_path}
        elif isinstance(self.owner, FolderComparator):
            content = {"status": status}
        else:
            raise ValueError("must be FolderChecker or FolderComparator")

        selection[self.owner.name] = content

        with open(self.save_path, "w", newline="\n") as f:
            json.dump(data, f, indent=4, sort_keys=True)

    def read(self):
        data = self.read_all()
        selection = self.select_data(data)
        return selection.get("status", "not_started")


class FolderChecker:
    data: pd.DataFrame | None = None
    structure = None
    error = "undefined"
    comparisons = {}

    def __init__(self, repo_path: Path | str, name: str | None = None):
        self.repo_path = Path(repo_path)
        self.name = self.get_save_name() if name is None else "calc_" + name
        self.foldername = self.name
        self.save_path = self.get_save_path()

        self.load()

    def get_save_path(self) -> Path:
        save_folder = Path(RESULTS_PATH)
        save_folder.mkdir(exist_ok=True, parents=True)
        return save_folder / f"{self.name}.pickle"

    def get_save_name(self) -> str:
        sha1 = hashlib.sha1()
        sha1.update(str(self.repo_path).encode())
        return sha1.hexdigest()[0:8]

    def save(self):
        print(f"saving {self}")
        if self.data is None:
            return False
        self.data.to_pickle(self.save_path)
        StatusFile(self).write(self.error)
        return True

    def load(self):
        print(f"loading {self}")
        if self.save_path.is_file():
            self.data = pd.read_pickle(self.save_path)
            return
        self.data = None

    def gather_files(self, mode=False):
        self.set_error("gather_error")

        self.structure = []
        print(f"Finding all files in the repo {self.repo_path}")
        for root, dirs, files in tqdm(self.repo_path.walk(), desc="Searching"):
            if not files:
                continue

            relative_dir = self.repo_path.relative_to(root)
            dirs = list(relative_dir.parts)
            dirs = [] if dirs == ["."] else dirs

            for file in files:
                file = Path(file)
                file_fullpath = Path(root) / file
                if mode:
                    if self.data is None:
                        raise ValueError("")
                    if file_fullpath in self.data.fullpath:
                        continue
                file_relpath = relative_dir / file
                name = file.stem
                ext = file.suffix
                ctime = file_fullpath.stat().st_ctime
                mtime = file_fullpath.stat().st_mtime
                time = ctime if ctime > mtime else mtime
                file_record = {
                    "filename": file,
                    "name": name,
                    "ext": ext,
                    "fullpath": str(file_fullpath),
                    "relpath": str(file_relpath),
                    "dirs": dirs,
                    "ctime": ctime,
                    "mtime": mtime,
                    "time": time,
                }

                file_record["uuid"] = deep_hash(file_record)
                self.structure.append(file_record)

        if len(self.structure) == 0:
            raise IOError(f"Found no files in {self.repo_path}")
        else:
            if mode:
                if self.data is None:
                    raise ValueError("")
                temp_data = pd.DataFrame(self.structure).set_index("uuid")
                self.data = pd.concat([self.data, temp_data]).drop_duplicates(
                    subset=["fullpath"], keep="first")
            else:
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
        return StatusFile(self).read()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            print("Traceback: ", "".join(
                traceback.format_exception(exc_type, exc_val, exc_tb))
            )

            if exc_type is IOError:
                self.set_error("no_file_error")
                return True

            if self.data is None:
                # data variable was not generated, investigate reasons
                if self.structure is None or len(self.structure) == 0:
                    # structure variable (pre-requisite of data) was also not set, crash was quite early
                    if not self.repo_path.is_dir():
                        # crash was due to repo not existing
                        raise IOError(
                            f"The folder {self.repo_path} does not exist")
                        # crash was due to another reason, logg it and raise
                    print(
                        f"error {exc_val} for {self} with traceback {exc_tb}")
                    return True  # propagate exception

                # structure exists, so build a (probably partial) data variable from it and save
                self.data = pd.DataFrame(self.structure).set_index("uuid")

            self.save()
            return True  # do not propagate exception
        else:
            # no problem occured
            if self.data is None:
                # data is none so either no class method was called in the context or a weird situation occured. Raising
                raise ValueError("")
            if "content_matches" in self.data.columns:
                # success case for partial run (first file info gathering part)
                self.set_error("comparison_success")
            else:
                # success case for hash calculation part from file contents
                self.set_error("run_success")

        self.save()

    def gather_hashes(self, mode=False):
        if self.data is None:
            raise ValueError("")
        if mode:
            if "hash" in self.data.columns:
                sel = self.data.hash.isna()
                if len(sel[sel]):
                    for index, row in tqdm(self.data.iterrows()):
                        if row.hash is None:
                            self.data.at[index, "hash"] = self.get_hash(
                                row.fullpath)
                return
        self.set_error("hashes_error")
        print(f"Claculating hashes for {len(self.data)} files :")
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

    def add_comparison(self, ref_folder):
        comp = FolderComparator(self, ref_folder)
        self.comparisons[ref_folder.name] = comp


class FolderComparator:
    _data = None
    error = "undefined"

    def __init__(self, current: FolderChecker, reference: FolderChecker):
        self.current = current
        self.reference = reference
        self.foldername = self.current.foldername

        self.name = self.current.name + "_vs_" + self.reference.name

        self.save_path = self.get_save_path()

    def get_save_path(self) -> Path:
        save_folder = Path(RESULTS_PATH)
        save_folder.mkdir(exist_ok=True, parents=True)
        return save_folder / f"{self.name}.pickle"

    def get_matches(self, cell, compared_data):
        matches = compared_data == cell
        matches = matches[matches]
        if len(matches):
            return matches.index.tolist()
        return []

    def set_error(self, error_name):
        self.error = error_name

    def get_error(self):
        return StatusFile(self).read()

    def compare(self, mode=False):
        self.set_error("comparison_error")

        if self.current.data is None or self.reference.data is None:
            raise ValueError(
                "Cannot compare with improperly instanciated FolderChecker")

        if self.get_error() != "comparison_success":
            print("Comparing names:")
            name_matches = self.current.data.relpath.progress_apply(
                self.get_matches, compared_data=self.reference.data.relpath
            )

        if self.get_error() != "comparison_success":
            print("Comparing hashes:")
            content_matches = self.current.data.hash.progress_apply(
                self.get_matches, compared_data=self.reference.data.hash
            )

        self._data = pd.DataFrame()
        self._data.index = self.current.data.index
        self._data["name_matches"] = name_matches
        self._data["content_matches"] = content_matches

    def save(self):
        print(f"saving {self}")
        if self._data is None:
            return False
        self._data.to_pickle(self.save_path)
        StatusFile(self).write(self.error)
        return True

    def load(self):
        print(f"loading {self}")
        if self.save_path.is_file():
            self._data = pd.read_pickle(self.save_path)
            return
        self._data = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            print("Traceback: ", "".join(
                traceback.format_exception(exc_type, exc_val, exc_tb)))
            return True  # do not propagate exception
        else:
            if self._data is None:
                raise ValueError("")
            self.set_error("run_success")

        self.save()

    @property
    def data(self):
        if self.current.data is None or self._data is None:
            raise ValueError(
                "Cannot load composite data from two FolderCheckers that are improperly instanciated")
        return pd.concat([self.current.data, self._data], axis=1)

    def _get_diffs(self, column, equal=True):
        def isempty(cell):
            return bool(len(cell)) if equal else not bool(len(cell))

        data = self.data

        selector = data[column].apply(isempty)
        return data[selector]

    def get_identical_files(self) -> pd.DataFrame:
        identical_contents = self._get_diffs("content_matches", True)
        identical_names = self._get_diffs("name_matches", True)

        sel = identical_names.index.isin(identical_contents.index)
        return identical_names[sel]

    def get_inexistant_files(self) -> pd.DataFrame:
        diff_contents = self._get_diffs("content_matches", False)
        diff_names = self._get_diffs("name_matches", False)

        sel = diff_names.index.isin(diff_contents.index)
        return diff_names[sel]

    def get_moved_files(self) -> pd.DataFrame:
        identical_contents = self._get_diffs("content_matches", True)
        diff_names = self._get_diffs("name_matches", False)

        sel = diff_names.index.isin(identical_contents.index)
        return diff_names[sel]

    def get_changed_files(self) -> pd.DataFrame:
        diff_contents = self._get_diffs("content_matches", False)
        identical_names = self._get_diffs("name_matches", True)

        sel = identical_names.index.isin(diff_contents.index)
        return identical_names[sel]

    def dates_results(self, result: pd.DataFrame) -> pd.DataFrame:
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
        result["most_recent"] = result.apply(
            is_most_recent, reference=self.reference.data, axis=1)

        return result

    def comparison_report(self) -> str:

        identical_contents = self.get_identical_files()
        inexistant_contents = self.get_inexistant_files()
        moved_contents = self.get_moved_files()
        changed_contents = self.get_changed_files()

        return (
            f"Report of contents for repo {self.current.name} at {self.current.repo_path}:\n
            f" - {len(self.data)} total files found.\n"
            f" - {len(identical_contents)} identical files (will be deleted)\n"
            f" - {len(inexistant_contents)} inexistant files (will be copied in main)\n"
            f" - {len(moved_contents)} moved files (same content, different location) (tbd)\n"
            f" - {len(changed_contents)} changed files (same location, different content) (tbd)\n"
        )


class FolderMerger:
    def __init__(self, main_repo: str, duplicates_repo: str | list = [], skip_checks=False):

        if not isinstance(duplicates_repo, list):
            duplicates_repo = [duplicates_repo]

        self.structs = {}

        self.structs["main"] = FolderChecker(main_repo)
        for index, repo_path in enumerate(duplicates_repo):
            self.structs[f"child_{index}"] = FolderChecker(repo_path)

        if skip_checks:
            return

        for struct in self.structs.values():
            with struct:
                struct.run()

        for name, struct in self.structs.items():
            if name == "main":
                continue
            struct.add_comparison(self.structs["main"])
            comp = struct.comparisons[self.structs["main"].name]
            with comp:
                comp.compare()

    @property
    def main(self):
        return self.structs["main"]

    def __str__(self):
        supps = "\n".join([f"{struct}" for struct in self.structs])
        return f"<GatherHashes with folders :\n{supps}>"

    def get_child(self, child_name=None):
        if child_name is None:
            child_name = [struct.name for key,
                          struct in self.structs.items() if key != "main"][0]
        elif isinstance(child_name, int):
            child_name = [struct.name for key, struct in self.structs.items(
            ) if key != "main"][child_name]
        got = [child for name, child in self.structs.items()
               if child.name == child_name]
        if len(got):
            return got[0]
        else:
            raise ValueError(f"No child with name {child_name}")

    def report(self):
        for name, struct in self.structs.items():
            if name == "main":
                continue
            struct.comparison_results()


if __name__ == "__main__":
    data = FolderMerger(r"C:\Users\Timothe\NasgoyaveOC\Projets",
                        [r"C:\Users\Timothe\NasgoyaveOC\Projets"])
    print(data)
    print(data.structs["main"])
    print(len(data.structs["main"].data))
    print(data.structs["child_0"])

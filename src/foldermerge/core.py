from pathlib import Path
import pandas as pd
import hashlib
from tqdm import tqdm
import json
import traceback
from typing import List, Dict, Literal, Callable, Any
import datetime

tqdm.pandas()


def get_default_results_path():
    return Path.home() / "Downloads" / "FILE_HASHES"


RESULTS_PATH = get_default_results_path()
BUF_SIZE = 65536
CROSS_INSTANCE_CACHED_HASH_DATA = {"cached_data": pd.DataFrame()}


def clear_results():
    results_path = Path(RESULTS_PATH)
    for item in results_path.iterdir():
        if item.is_file():
            item.unlink()


class StageMixin:

    error: str = "undefined"
    name: str
    _data: pd.DataFrame

    def __enter__(self):
        return self

    def __str__(self):
        repo_path = getattr(self, "repo_path", "")
        repo_path = f" at {repo_path}" if repo_path else ""
        return f"<{self.__class__.__name__} {self.name}{repo_path}>"

    @property
    def data(self):
        return self._data

    @property
    def save_path(self) -> Path:
        save_folder = Path(RESULTS_PATH)
        save_folder.mkdir(exist_ok=True, parents=True)
        return save_folder / f"{self.name}.pickle"

    def set_error(self, error_name):
        self.error = error_name

    def get_error(self):
        return StatusFile(self).read()

    def load(self):
        print(f"loading {self}")
        if self.save_path.is_file():
            self._data = pd.read_pickle(self.save_path)
            return
        self._data = pd.DataFrame()

    def save(self):
        print(f"saving {self}")
        if self._data.empty:
            return False
        self._data.to_pickle(self.save_path)
        StatusFile(self).write(self.error)
        return True


class StatusFile:
    """Data stored as :
    {
        group_key : {
            category_key : {
                <optional_name_key : {>
                    status_content_dict
                }
            }
        }
    }
    """

    settings = {
        "FolderChecker": {
            "group_key": lambda x: getattr(getattr(x, "owner"), "name"),
            "category_key": "checks",
            "use_name_key": False,
        },
        "FolderComparator": {
            "group_key": lambda x: getattr(getattr(getattr(x, "owner"), "current"), "name"),
            "category_key": "comparison",
            "use_name_key": True,
        },
        "HashLibrary": {
            "group_key": "general",
            "category_key": "hashes",
            "use_name_key": False,
        },
    }

    owner: StageMixin

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
            try:
                return json.load(f)
            except Exception:
                with open(self.save_path, "r") as f_in:
                    filename = datetime.datetime.now().strftime("status_error_backup_%y%m%d.json")
                    with open(self.save_path.parent / filename, "w") as f_out:
                        f_out.write(f_in.read())
                print(f"Could not decode the json results file. All contents have been backuped to {filename}")
                return {}

    def _map_setting(self, key):
        try:
            value = self.settings[self.owner.__class__.__name__][key]
            if isinstance(value, Callable):
                value = value(self)
            return value
        except KeyError:
            raise ValueError(f"{self.owner.__class__}-{key} is not specified in StatusFile settings")

    @property
    def group_key(self) -> str:
        return self._map_setting("group_key")

    @property
    def category_key(self) -> str:
        return self._map_setting("category_key")

    @property
    def use_name_key(self) -> bool:
        return bool(self._map_setting("use_name_key"))

    @property
    def name_key(self) -> str:
        return self.owner.name

    @property
    def selection_key(self):
        return self.name_key if self.use_name_key else self.category_key

    def content(self, status):
        if isinstance(self.owner, FolderChecker):
            content = {"status": status, "path": str(self.owner.repo_path)}
        else:
            content = {"status": status}
        return content

    def select_data(self, data):

        selection = data.get(self.group_key, {})
        data.update({self.group_key: selection})

        if self.use_name_key:
            # select and update with current obj dict, the key of the action (check, compare)
            selection = selection.get(self.category_key, {})
            data[self.group_key].update({self.category_key: selection})

        return selection

    def write(self, status):
        data = self.read_all()

        selection = self.select_data(data)
        selection[self.selection_key] = self.content(status)

        with open(self.save_path, "w", newline="\n") as f:
            json.dump(data, f, indent=4, sort_keys=True)

    def read(self):
        data = self.read_all()
        selection = self.select_data(data)
        return selection.get(self.selection_key, {}).get("status", "not_started")


class HashLibrary(StageMixin):

    entries_buffer: list

    cross_instance_cached_data: Dict[str, pd.DataFrame] = CROSS_INSTANCE_CACHED_HASH_DATA

    def __init__(self, cached=False):
        self.entries_buffer = []

        self.name = "hash_library"

        if cached:
            self.recover_cached_data()
        else:
            self.load()

    def __enter__(self):
        self.set_error("hash_gathering_error")
        self.entries_buffer = []
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.set_error("hash_gathering_success")
        self.update_library()
        self.save()
        self.set_cached_data()

    def load(self):
        super().load()
        if self._data.empty:
            self._data = pd.DataFrame(columns=["hash"])

    def retrieve_entry(self, row: pd.Series) -> str:
        uuid = row.name if row.name is not None else row["uuid"]
        if uuid in self.data.index:
            return str(self.data.loc[uuid, "hash"])  # pyright: ignore
        # print("unable to retrieve from store")
        hash = self.get_hash(row.fullpath)
        self.add_entry(row, hash)
        return hash

    def get_hash(self, path: str):
        sha1 = hashlib.sha1()
        with open(path, "rb") as f:
            while True:
                content = f.read(BUF_SIZE)
                if not content:
                    break
                sha1.update(content)
        return sha1.hexdigest()

    def add_entry(self, row: pd.Series, hash: str):
        name = row.name if row.name is not None else row["uuid"]
        new_row = pd.Series(
            {"fullpath": row["fullpath"], "hash": hash, "ctime": row.ctime, "mtime": row.mtime}, name=name
        )
        self.entries_buffer.append(new_row)

    def update_library(self):
        if len(self.entries_buffer):
            if self.data.empty:
                data = pd.DataFrame(self.entries_buffer)
                data.index.name = "uuid"
            else:
                data = pd.concat([self.data, pd.DataFrame(self.entries_buffer)])
                data = data.drop_duplicates(keep="last")
            self._data = data
            self.entries_buffer = []

    def recover_cached_data(self):
        self._data = self.cross_instance_cached_data["cached_data"]

    def set_cached_data(self):
        self.cross_instance_cached_data["cached_data"] = self._data


class FolderChecker(StageMixin):

    entries_buffer: list
    comparisons: Dict[str, "FolderComparator"]
    is_reference: bool = False

    def __init__(self, repo_path: Path | str):
        self.repo_path = Path(repo_path)

        sha1 = hashlib.sha1()
        sha1.update(str(self.repo_path).encode())
        self.name = sha1.hexdigest()[0:8]

        self.comparisons = {}

        self.load()

    def __enter__(self):
        self.entries_buffer = []
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            print("Traceback: ", "".join(traceback.format_exception(exc_type, exc_val, exc_tb)))
        else:
            self.set_error("complete_success")

        if len(self.entries_buffer):
            if not self.data.empty:
                # later, implement a merge between old data got by load and new data obtained with scan
                # do not save for now
                return
            else:
                self._data = pd.DataFrame(self.entries_buffer).set_index("uuid")
                self.entries_buffer = []
        else:
            if self.data.empty:
                # unknown reason crash, logg it
                print(f"error {exc_val} for {self} with traceback {exc_tb}")

        self.save()

    def run(self, refresh=True):
        if self._data.empty or refresh:
            self.gather_files()
            self.gather_hashes()

    @staticmethod
    def get_uuid(data: Any) -> int:
        sha = hashlib.sha1()
        sha.update(json.dumps(data).encode())
        return int(sha.hexdigest(), 16)

    def gather_files(self):

        self.set_error("gather_error")

        print(f"Finding all files in the repo {self.repo_path}")
        if not self.repo_path.is_dir():
            self.set_error("directory_access_error")
            raise OSError(f"Path {self.repo_path} doesn't lead to an accessible directory")

        for root, dirs, files in tqdm(self.repo_path.walk(), desc="Searching"):
            if not files:
                continue

            relative_dir = root.relative_to(self.repo_path)
            dirs = list(relative_dir.parts)
            dirs = [] if dirs == ["."] else dirs

            for file in files:
                file = Path(file)
                file_fullpath = Path(root) / file

                file_relpath = relative_dir / file
                name = file.stem
                ext = file.suffix
                ctime = file_fullpath.stat().st_ctime
                mtime = file_fullpath.stat().st_mtime
                time = ctime if ctime > mtime else mtime

                filesize = file_fullpath.stat().st_size

                file_record = {"fullpath": str(file_fullpath), "ctime": ctime, "mtime": mtime, "time": time}
                file_record["uuid"] = self.get_uuid(file_record)
                file_record.update(
                    {
                        "filename": str(file),
                        "name": name,
                        "ext": ext,
                        "relpath": str(file_relpath),
                        "reldirpath": str(relative_dir),
                        "dirs": dirs,
                        "filesize": filesize,
                    }
                )

                self.entries_buffer.append(file_record)

        if len(self.entries_buffer) == 0:
            self.set_error("no_file_error")
            raise OSError(f"Found no files in {self.repo_path}")
        else:
            self._data = pd.DataFrame(self.entries_buffer).set_index("uuid")
            self.entries_buffer = []

        self.set_error("check_success")

    def gather_hashes(self):

        hlib = HashLibrary()

        if self.data.empty:
            raise ValueError(f"Cannot get hash for empty folder {self.name}")

        self.set_error("hashes_error")
        print(f"Claculating hashes for {len(self.data)} files :")
        with hlib:
            self.data["hash"] = self.data.progress_apply(hlib.retrieve_entry, axis=1)  # type: ignore

    def add_comparison(self, ref_folder):
        comparison = FolderComparator(self, ref_folder)
        self.comparisons[ref_folder.name] = comparison

    def report(self, mode: Literal["text", "dict"] = "text") -> str | dict:

        if mode == "dict":
            return {"repo_path": self.repo_path, "total_files": len(self.data), "name": self.name}
        elif mode == "text":
            return (
                f"Report of contents for folder {self.name} at {self.repo_path}\n"
                f"{len(self.data)} total files found."
            )
        else:
            raise ValueError("unknown mode")


class FolderComparator(StageMixin):

    def __init__(self, current: FolderChecker, reference: FolderChecker):
        self.current = current  # main folder
        self.reference = reference  # child folder

        self.name = self.current.name + "_vs_" + self.reference.name

        self.load()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            print("Traceback: ", "".join(traceback.format_exception(exc_type, exc_val, exc_tb)))
            return True  # do not propagate exception
        else:
            if self._data.empty:
                raise ValueError("")
            self.set_error("run_success")

        self.save()

    def get_matches(self, cell, compared_data):
        matches = compared_data == cell
        matches = matches[matches]
        if len(matches):
            return matches.index.tolist()
        return []

    def gather_comparisons(self):
        self.set_error("comparison_error")

        if self.current.data is None or self.reference.data is None:
            raise ValueError("Cannot compare with improperly instanciated FolderChecker")

        # if self.get_error() != "comparison_success":
        print("Comparing names:")
        name_matches = self.current.data.relpath.progress_apply(
            self.get_matches, compared_data=self.reference.data.relpath
        )

        # if self.get_error() != "comparison_success":
        print("Comparing hashes:")
        content_matches = self.current.data.hash.progress_apply(
            self.get_matches, compared_data=self.reference.data.hash
        )

        rows = list(zip(name_matches, content_matches, ["undefined"] * len(self.current.data)))

        self._data = pd.DataFrame(
            data=rows,
            columns=["name_matches", "content_matches", "action"],
            index=self.current.data.index,
        )

    @property
    def data(self):
        if self.current.data is None or self._data.empty:
            raise ValueError("Cannot load composite data from two FolderCheckers that are improperly instanciated")

        return ComparisonResult.from_folder_comparator(
            pd.concat([self.current.data, self._data], axis=1), "all_files", self
        )

    def run(self, refresh=True):
        if self._data.empty or refresh:
            self.gather_comparisons()

    def compare(self, column: str, equal=True) -> pd.DataFrame:
        def isempty(cell):
            return bool(len(cell)) if equal else not bool(len(cell))

        data = self.data  # build data merge

        selector = data[column].progress_apply(isempty)
        return data[selector]

    def get_identical_files(self) -> pd.DataFrame:
        identical_contents = self.compare("content_matches", True)
        identical_names = self.compare("name_matches", True)

        sel = identical_names.index.isin(identical_contents.index)
        return ComparisonResult.from_folder_comparator(identical_names[sel], "identical_files", self)

    def get_inexistant_files(self) -> pd.DataFrame:
        diff_contents = self.compare("content_matches", False)
        diff_names = self.compare("name_matches", False)

        sel = diff_names.index.isin(diff_contents.index)
        return ComparisonResult.from_folder_comparator(diff_names[sel], "different_files", self)

    def get_moved_files(self) -> pd.DataFrame:
        identical_contents = self.compare("content_matches", True)
        diff_names = self.compare("name_matches", False)

        sel = diff_names.index.isin(identical_contents.index)
        return ComparisonResult.from_folder_comparator(diff_names[sel], "renamed_files", self)

    def get_changed_files(self) -> pd.DataFrame:
        diff_contents = self.compare("content_matches", False)
        identical_names = self.compare("name_matches", True)

        sel = identical_names.index.isin(diff_contents.index)
        return ComparisonResult.from_folder_comparator(identical_names[sel], "modified_files", self)

    def get_files(self, selection) -> pd.DataFrame:
        if selection == "identical":
            return self.get_identical_files()
        elif selection == "inexistant":
            return self.get_inexistant_files()
        elif selection == "moved":
            return self.get_moved_files()
        elif selection == "changed":
            return self.get_changed_files()
        elif selection == "all":
            return self.data
        else:
            raise ValueError(f"Cannot access the selection {selection}")

    # def dates_results(self, result: pd.DataFrame) -> pd.DataFrame:
    #     def is_most_recent(row, reference):
    #         ref_ix = row.name_matches[0]
    #         ref_row = reference.loc[ref_ix]

    #         return (row.ctime > ref_row.ctime, row.mtime > ref_row.mtime, row.time > ref_row.time)

    #     def most_recent_no_ambiguity(cell):
    #         # returns True if all the metric are more recent in the child vs main. Otherwise, False
    #         return all(cell)

    #     def most_old_no_ambiguity(cell):
    #         # returns True if any of the metric is more recent in the child vs main. Otherwise False
    #         return not any(cell)

    #     result = result.copy()
    #     result["most_recent"] = result.apply(is_most_recent, reference=self.reference.data, axis=1)

    #     return result

    def report(self, mode: Literal["text", "dict"] = "text") -> str | dict:

        identical_contents = self.get_identical_files()
        inexistant_contents = self.get_inexistant_files()
        moved_contents = self.get_moved_files()
        changed_contents = self.get_changed_files()

        if mode == "dict":
            return {
                "compared_repo": self.current.repo_path,
                "reference_repo": self.reference.repo_path,
                "total_files": len(self.data),
                "identical_content": len(identical_contents),
                "inexistant_content": len(inexistant_contents),
                "moved_contents": len(moved_contents),
                "changed_contents": len(changed_contents),
                "name": self.current.name,
            }

        elif mode == "text":
            return (
                f"Report of contents for folder {self.current.name} at {self.current.repo_path} "
                f"compared to reference folder at {self.reference.repo_path}:\n"
                f" - {len(self.data)} total files found.\n"
                f" - {len(identical_contents)} identical files (will be deleted)\n"
                f" - {len(inexistant_contents)} inexistant files (will be copied in main)\n"
                f" - {len(moved_contents)} moved files (same content, different location) (tbd)\n"
                f" - {len(changed_contents)} changed files (same location, different content) (tbd)\n"
            )
        else:
            raise ValueError("unknown mode")


class ComparisonResult(pd.DataFrame):

    _metadata = ["reference", "current", "parent", "comp_type"]

    @property
    def _constructor(self):
        return ComparisonResult

    @staticmethod
    def from_folder_comparator(data: pd.DataFrame, type: str, parent: FolderComparator) -> "ComparisonResult":
        obj = ComparisonResult(data)
        obj.reference = parent.reference
        obj.current = parent.current
        obj.parent = parent
        obj.comp_type = type
        return obj


class Folders(dict[str, FolderChecker]):
    """Just an utility to better organize multiples folders in a FolderComparator
    It is a custom dictionnary that keeps folders organization and relationship between each other.
    """

    def __init__(self, dico={}):
        super().__init__(dico)

    def __getitem__(self, index: int | str | slice) -> FolderChecker | Dict[str, FolderChecker]:
        if isinstance(index, int):
            return super().__getitem__(list(self.keys())[index])
        elif isinstance(index, slice):
            dico = {}
            for ix in range(index.start or 0, index.stop or len(self), index.step or 1):
                value = self[ix]
                if isinstance(value, FolderChecker):
                    dico[value.name] = value
            return dico
        else:
            return super().__getitem__(index)

    def __setitem__(self, index: int | str, value: FolderChecker):
        if isinstance(index, int):
            index = value.name
        super().__setitem__(index, value)

    def child(self, number: int) -> FolderChecker:
        out = self[number + 1]
        if not isinstance(out, FolderChecker):
            raise ValueError
        return out

    def named(self, reference: str) -> FolderChecker:
        """Finds the folder named like argument, from the dictionnary of folders.

        Args:
            reference (str): name to search for

        Raises:
            ValueError: If name not found

        Returns:
            FolderChecker
        """
        out = self[reference]
        if not isinstance(out, FolderChecker):
            raise ValueError
        return out

    def add(self, folder: FolderChecker):
        self[folder.name] = folder
        if len(self) == 1:
            self[folder.name].is_reference = True

    @property
    def main(self) -> FolderChecker:
        out = self[0]
        if not isinstance(out, FolderChecker):
            raise ValueError
        return out

    @property
    def childs(self) -> Dict[str, FolderChecker]:
        out = self[1:]
        if not isinstance(out, dict):
            raise ValueError
        return out


class FolderMerger:
    def __init__(self, destination_repo: str | Path, sources_repo: str | Path | List[str | Path] = [], refresh=False):

        if not isinstance(sources_repo, list):
            sources_repo = [sources_repo]

        self.folders = Folders()

        self.folders.add(FolderChecker(destination_repo))
        for repo_path in sources_repo:
            self.folders.add(FolderChecker(repo_path))

        for folder_checker in self.folders.values():
            with folder_checker:
                folder_checker.run(refresh)

        for folder_checker in self.folders.childs.values():
            folder_checker.add_comparison(self.folders.main)
            folder_comparator = folder_checker.comparisons[self.folders.main.name]
            with folder_comparator:
                folder_comparator.run(refresh)

    def __str__(self):
        supps = "\n".join([f"{folder}" for folder in self.folders])
        return f"<GatherHashes with folders :\n{supps}>"

    def report(self, mode: Literal["text", "dict"] = "text") -> List[str | dict]:
        reports = []
        for folder in self.folders.childs.values():
            reports.append(folder.comparisons[self.folders.main.name].report(mode))
        return reports

    def serialize(self):
        return {
            "reference_folder": self.folders.main.repo_path,
            "compared_folders": [child.repo_path for child in self.folders.childs.values()],
        }


if __name__ == "__main__":
    data = FolderMerger(r"C:\Users\Timothe\NasgoyaveOC\Projets", [r"C:\Users\Timothe\NasgoyaveOC\Projets"])
    print(data)
    print(data.folders.main)
    print(len(data.folders.main.data))
    print(data.folders.child(0))

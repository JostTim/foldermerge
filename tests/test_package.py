import pytest
from pathlib import Path
import foldermerge

foldermerge.core.RESULTS_PATH = (Path(__file__).parent / "results").absolute()


@pytest.fixture
def fixtures_folder():
    return (Path(__file__).parent / "integration" / "fixtures").absolute()


@pytest.fixture
def mainfolder(fixtures_folder):
    return fixtures_folder / "mainfolder"


@pytest.fixture
def dupefolder1(fixtures_folder):
    return fixtures_folder / "dupefolder1"


@pytest.fixture(scope="session")
def merger(mainfolder, dupefolder1):
    return foldermerge.FolderMerger(mainfolder, [dupefolder1])


class TestIntegration:

    def class_creation(self, merger):
        merger = 


class TestErrors:

    def unknown_directory(self, fixtures_folder):
        directory = fixtures_folder / "directory_unknown"
        with pytest.raises(IOError):
            foldermerge.FolderMerger(directory)

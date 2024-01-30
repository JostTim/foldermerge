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


class TestIntegration:
    def test_full_pipeline(self, mainfolder, dupefolder1):
        fm = foldermerge.FolderMerger(mainfolder, [dupefolder1])

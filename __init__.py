from . core import FolderMerger
import logging
import sys

LOGGER = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(' %(levelname)-8s : %(message)s')
handler.setFormatter(formatter)
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(handler)


def console():
    LOGGER.info("RUNNING FOLDER MERGE.py")
    try:
        main = str(sys.argv[1])
    except IndexError:
        raise ValueError(
            "Must supply at least one folder, a 'main', as first argument")
    LOGGER.info(f"Main is {main}")
    supplementaries = []
    i = 2
    while True:
        try:
            temp = str(sys.argv[i])
            supplementaries.append(temp)
            LOGGER.info("Got a supplementary {temp}")
            i += 1
        except IndexError:
            break

    FolderMerger(main, supplementaries)


if __name__ == "__main__":
    console()

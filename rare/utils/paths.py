import os
import shutil
from pathlib import Path

from PyQt5.QtCore import QStandardPaths

resources_path = Path(__file__).absolute().parent.parent.joinpath("resources")

# lk: delete old Rare directories
for old_dir in [
    Path(QStandardPaths.writableLocation(QStandardPaths.CacheLocation), "rare").joinpath("tmp"),
    Path(QStandardPaths.writableLocation(QStandardPaths.DataLocation), "rare").joinpath("images"),
    Path(QStandardPaths.writableLocation(QStandardPaths.CacheLocation), "rare"),
    Path(QStandardPaths.writableLocation(QStandardPaths.DataLocation), "rare"),
]:
    if old_dir.exists():
        # lk: case-sensitive matching on Winblows
        if old_dir.stem in os.listdir(old_dir.parent):
            shutil.rmtree(old_dir, ignore_errors=True)


# lk: TempLocation doesn't depend on OrganizationName or ApplicationName
# lk: so it is fine to use it before initializing the QApplication
def lock_file() -> Path:
    return Path(QStandardPaths.writableLocation(QStandardPaths.TempLocation), "Rare.lock")


def data_dir() -> Path:
    return Path(QStandardPaths.writableLocation(QStandardPaths.DataLocation))


def cache_dir() -> Path:
    return Path(QStandardPaths.writableLocation(QStandardPaths.CacheLocation))


def image_dir() -> Path:
    return data_dir().joinpath("images")


def log_dir() -> Path:
    return cache_dir().joinpath("logs")


def tmp_dir() -> Path:
    return cache_dir().joinpath("tmp")


def create_dirs() -> None:
    for path in (data_dir(), cache_dir(), image_dir(), log_dir(), tmp_dir()):
        if not path.exists():
            path.mkdir(parents=True)

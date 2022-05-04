from pathlib import Path

from PyQt5.QtCore import QStandardPaths

resources_path = Path(__file__).absolute().parent.parent.joinpath("resources")
data_dir = Path(QStandardPaths.writableLocation(QStandardPaths.DataLocation), "rare")
cache_dir = Path(QStandardPaths.writableLocation(QStandardPaths.CacheLocation), "rare")
image_dir = data_dir.joinpath("images")
tmp_dir = cache_dir.joinpath("tmp")

for path in (data_dir, cache_dir, image_dir, tmp_dir):
    if not path.exists():
        path.mkdir(parents=True)

import os
import pathlib
from PyQt5.QtCore import QStandardPaths

resources_path = pathlib.Path(__file__).absolute().parent.parent.joinpath("resources")
data_dir = os.path.join(QStandardPaths.writableLocation(QStandardPaths.DataLocation), "rare")
cache_dir = os.path.join(QStandardPaths.writableLocation(QStandardPaths.CacheLocation), "rare")
image_dir = os.path.join(data_dir, "images")
tmp_dir = os.path.join(cache_dir, "tmp")

for path in (data_dir, cache_dir, image_dir, tmp_dir):
    if not os.path.exists(path):
        os.makedirs(path)

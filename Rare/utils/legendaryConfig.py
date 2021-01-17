import configparser
import os

from legendary.lfs.lgndry import LGDLFS

lgd = LGDLFS()

def get_config() -> {}:
    return lgd.config

def set_config(new_config: {}):
    lgd.config = new_config
    with open(os.path.join(lgd.path, 'config.ini'), "w") as cf:
        lgd.config.write(cf)

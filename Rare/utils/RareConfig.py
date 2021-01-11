import configparser
import os
from logging import getLogger

config_path = os.path.join(os.path.expanduser("~"), ".config/Rare/")
rare_config = configparser.ConfigParser()

logger = getLogger("Config")
rare_config.read(config_path + "config.ini")

if not os.path.exists(config_path):
    os.makedirs(config_path)
    rare_config["Rare"] = {
        "IMAGE_DIR": os.path.expanduser("~/.cache/images"),
        "theme": "dark"
    }
    rare_config.write(open(config_path + "config.ini", "w"))
elif not rare_config.sections():
    rare_config["Rare"] = {
        "IMAGE_DIR": os.path.expanduser("~/.cache/images"),
        "theme": "dark"
    }
    rare_config.write(open(config_path + "config.ini", "w"))


def get_config() -> {}:
    return rare_config.__dict__["_sections"]


def set_config(new_config: {}):
    rare_config.__dict__["_sections"] = new_config
    rare_config.write(open(config_path + "config.ini", "w"))


IMAGE_DIR = rare_config["Rare"]["IMAGE_DIR"]
THEME = rare_config["Rare"]["theme"]

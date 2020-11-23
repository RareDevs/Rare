import configparser
import os

config_path = os.path.join(os.path.expanduser("~"), ".config/Rare/")
rare_config = configparser.ConfigParser()

if not os.path.exists(config_path):
    rare_config["Rare"] = {
        "image_dir": "../",
        "theme": "dark"
    }
else:
    rare_config.read(config_path + "config.ini")
print(rare_config.__dict__)


def get_config() -> {}:
    return rare_config.__dict__["_sections"]


def set_config(new_config: {}):
    rare_config.__dict__["_sections"] = new_config
    rare_config.write(open(config_path + "config.ini", "w"))

import configparser
import os

config_path = os.path.expanduser("~") + "/.config/legendary/"
lgd_config = configparser.ConfigParser()
lgd_config.read(config_path + "config.ini")


def get_config() -> {}:
    print(lgd_config.__dict__["_sections"])
    return lgd_config.__dict__["_sections"]


def set_config(new_config: {}):
    lgd_config.__dict__["_sections"] = new_config
    lgd_config.write(open(config_path + "config.ini", "w"))

import configparser
import os

config_path = os.path.expanduser("~") + "/.config/legendary/"
lgd_config = configparser.ConfigParser()
lgd_config.optionxform = str


def get_config() -> {}:
    lgd_config.read(config_path + "config.ini")
    lgd_config.optionxform = str
    return lgd_config


def set_config(new_config: {}):
    lgd_config = new_config
    lgd_config.write(open(config_path + "config.ini", "w"))

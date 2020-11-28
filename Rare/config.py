import configparser
import logging
import os

config_path = os.path.expanduser("~") + "/.config/Rare"

cfg = configparser.ConfigParser()
cfg.read(os.path.expanduser("~") + "/.config/Rare")

logger = logging.getLogger("Config")

if not os.path.exists(config_path):
    os.mkdir(config_path)
    logger.info("Create Config dir")

if not cfg.sections():
    cfg["Rare"] = {
        "IMAGE_DIR": "../images",
        "LOGLEVEL": logging.INFO
    }

with open(config_path + '/Rare.ini', 'w') as configfile:
    cfg.write(configfile)

IMAGE_DIR = cfg["Rare"]["IMAGE_DIR"]
LOGLEVEL = cfg["Rare"]["LOGLEVEL"]

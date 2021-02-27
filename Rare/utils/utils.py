import json
import os
import shutil
from logging import getLogger

import requests
from PIL import Image
from PyQt5.QtCore import pyqtSignal, QLocale, QSettings
from legendary.core import LegendaryCore

from Rare import lang_path
from Rare.utils import legendaryConfig

logger = getLogger("Utils")
s = QSettings("Rare","Rare")
IMAGE_DIR = s.value("img_dir", os.path.expanduser("~/.cache/rare"), type=str)
logger.info("IMAGE DIRECTORY: "+IMAGE_DIR)

def download_images(signal: pyqtSignal, core: LegendaryCore):
    if not os.path.isdir(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)
        logger.info("Create Image dir")

    # Download Images
    for i, game in enumerate(sorted(core.get_game_list(), key=lambda x: x.app_title)):

        try:
            download_image(game)
        except json.decoder.JSONDecodeError:
            shutil.rmtree(f"{IMAGE_DIR}/{game.app_name}")
            download_image(game)
        signal.emit(i)


def download_image(game, force=False):
    if force:
        shutil.rmtree(f"{IMAGE_DIR}/{game.app_name}")
    if not os.path.isdir(f"{IMAGE_DIR}/" + game.app_name):
        os.mkdir(f"{IMAGE_DIR}/" + game.app_name)

    if not os.path.isfile(f"{IMAGE_DIR}/{game.app_name}/image.json"):
        json_data = {"DieselGameBoxTall": None, "DieselGameBoxLogo": None}
    else:
        json_data = json.load(open(f"{IMAGE_DIR}/{game.app_name}/image.json", "r"))
    # Download
    for image in game.metadata["keyImages"]:
        if image["type"] == "DieselGameBoxTall" or image["type"] == "DieselGameBoxLogo":

            if json_data[image["type"]] != image["md5"] or not os.path.isfile(
                    f"{IMAGE_DIR}/{game.app_name}/{image['type']}.png"):
                # Download
                json_data[image["type"]] = image["md5"]
                # os.remove(f"{IMAGE_DIR}/{game.app_name}/{image['type']}.png")
                json.dump(json_data, open(f"{IMAGE_DIR}/{game.app_name}/image.json", "w"))
                logger.info(f"Download Image for Game: {game.app_title}")
                url = image["url"]
                with open(f"{IMAGE_DIR}/{game.app_name}/{image['type']}.png", "wb") as f:
                    f.write(requests.get(url).content)
                    f.close()
    # scale and grey
    if not os.path.isfile(f'{IMAGE_DIR}/' + game.app_name + '/UninstalledArt.png'):

        if os.path.isfile(f'{IMAGE_DIR}/' + game.app_name + '/DieselGameBoxTall.png'):
            # finalArt = Image.open(f'{IMAGE_DIR}/' + game.app_name + '/DieselGameBoxTall.png')
            # finalArt.save(f'{IMAGE_DIR}/{game.app_name}/FinalArt.png')
            # And same with the grayscale one

            bg = Image.open(f"{IMAGE_DIR}/{game.app_name}/DieselGameBoxTall.png")
            uninstalledArt = bg.convert('L')
            uninstalledArt.save(f'{IMAGE_DIR}/{game.app_name}/UninstalledArt.png')
        elif os.path.isfile(f"{IMAGE_DIR}/{game.app_name}/DieselGameBoxLogo.png"):
            bg: Image.Image = Image.open(f"{IMAGE_DIR}/{game.app_name}/DieselGameBoxLogo.png")
            bg = bg.resize((int(bg.size[1] * 3 / 4), bg.size[1]))
            logo = Image.open(f'{IMAGE_DIR}/{game.app_name}/DieselGameBoxLogo.png').convert('RGBA')
            wpercent = ((bg.size[0] * (3 / 4)) / float(logo.size[0]))
            hsize = int((float(logo.size[1]) * float(wpercent)))
            logo = logo.resize((int(bg.size[0] * (3 / 4)), hsize), Image.ANTIALIAS)
            # Calculate where the image has to be placed
            pasteX = int((bg.size[0] - logo.size[0]) / 2)
            pasteY = int((bg.size[1] - logo.size[1]) / 2)
            # And finally copy the background and paste in the image
            # finalArt = bg.copy()
            # finalArt.paste(logo, (pasteX, pasteY), logo)
            # Write out the file
            # finalArt.save(f'{IMAGE_DIR}/' + game.app_name + '/FinalArt.png')
            logoCopy = logo.copy()
            logoCopy.putalpha(int(256 * 3 / 4))
            logo.paste(logoCopy, logo)
            uninstalledArt = bg.copy()
            uninstalledArt.paste(logo, (pasteX, pasteY), logo)
            uninstalledArt = uninstalledArt.convert('L')
            uninstalledArt.save(f'{IMAGE_DIR}/' + game.app_name + '/UninstalledArt.png')
        else:
            logger.warning(f"File {IMAGE_DIR}/{game.app_name}/DieselGameBoxTall.png dowsn't exist")


def get_lang():
    if "Legendary" in legendaryConfig.get_config() and "locale" in legendaryConfig.get_config()["Legendary"]:
        logger.info("Found locale in Legendary config: " + legendaryConfig.get_config()["Legendary"]["locale"])
        return legendaryConfig.get_config()["Legendary"]["locale"].split("-")[0]
    else:
        logger.info("Found locale in system config: " + QLocale.system().name().split("_")[0])
        return QLocale.system().name().split("_")[0]


def get_possible_langs():
    langs = ["en"]
    for i in os.listdir(lang_path):
        if i.endswith(".qm"):
            langs.append(i.split(".")[0])
    return langs

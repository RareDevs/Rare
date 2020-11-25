import os
from logging import getLogger

import requests
from PIL import Image
from PyQt5.QtCore import pyqtSignal

from Rare.utils import legendaryUtils

logger = getLogger("Utils")


def download_images(signal: pyqtSignal):
    IMAGE_DIR = "../images"
    if not os.path.isdir(IMAGE_DIR):
        os.mkdir(IMAGE_DIR)
        logger.info("Create Image dir")

    # Download Images

    for i, game in enumerate(legendaryUtils.get_games()):
        for image in game.metadata["keyImages"]:
            if image["type"] == "DieselGameBoxTall" or image["type"] == "DieselGameBoxLogo":
                if not os.path.isfile(f"{IMAGE_DIR}/{game.app_name}/{image['type']}.png"):
                    if not os.path.isdir(f"{IMAGE_DIR}/" + game.app_name):
                        os.mkdir(f"{IMAGE_DIR}/" + game.app_name)

                    logger.info(f"Download Image for Game: {game.app_title}")
                    url = image["url"]
                    with open(f"{IMAGE_DIR}/{game.app_name}/{image['type']}.png", "wb") as f:
                        f.write(requests.get(url).content)
                        f.close()

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
        signal.emit(i)

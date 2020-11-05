import logging
import os
import sys

import requests
from PIL import Image
from PyQt5.QtWidgets import QTabWidget, QMainWindow, QWidget, QApplication

from Rare.Dialogs import LoginDialog
from Rare.TabWidgets import Settings, GameListInstalled, BrowserTab, GameListUninstalled, UpdateList
from Rare.config import IMAGE_DIR
from Rare.utils import legendaryUtils

logging.basicConfig(
    format='[%(name)s] %(levelname)s: %(message)s',
)
logger = logging.getLogger("Rare")


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rare")
        self.setGeometry(0, 0, 800, 600)
        self.setCentralWidget(TabWidget(self))
        self.show()


class TabWidget(QTabWidget):

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)

        self.game_list = GameListInstalled(self)
        self.addTab(self.game_list, "Games")

        self.uninstalled_games = GameListUninstalled(self)
        self.addTab(self.uninstalled_games, "Install Games")

        self.update_tab = UpdateList(self)
        self.addTab(self.update_tab, "Updates")

        self.browser = BrowserTab(self)
        self.addTab(self.browser, "Store")

        self.settings = Settings(self)
        self.addTab(self.settings, "Settings")


def main():
    app = QApplication(sys.argv)
    if os.path.isfile(os.path.expanduser("~") + '/.config/legendary/user.json'):
        logger.info("Launching Rare")
        download_images()
    else:
        dia = LoginDialog()
        code = dia.get_login()
        if code == 1:
            app.closeAllWindows()
            logger.info("Exit login")
            exit(0)
        elif code == 0:
            logger.info("Login successfully")

    window = MainWindow()
    app.exec_()


def download_images():
    if not os.path.isdir(IMAGE_DIR):
        os.mkdir(IMAGE_DIR)
        logger.info("Create Image dir")

    # Download Images
    for game in legendaryUtils.get_games():
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

        if not os.path.isfile(f"{IMAGE_DIR}/{game.app_name}/FinalArt.png"):
            logger.info("Scaling cover for " + game.app_name)
            if os.path.isfile(f"{IMAGE_DIR}/{game.app_name}/DieselGameBoxLogo"):
                bg: Image.Image = Image.open()
                bg = bg.resize((int(bg.size[1] * 3 / 4), bg.size[1]))
                logo = Image.open('images/' + game["app_name"] + '/DieselGameBoxLogo.png').convert('RGBA')
                wpercent = ((bg.size[0] * (3 / 4)) / float(logo.size[0]))
                hsize = int((float(logo.size[1]) * float(wpercent)))
                logo = logo.resize((int(bg.size[0] * (3 / 4)), hsize), Image.ANTIALIAS)
                # Calculate where the image has to be placed
                pasteX = int((bg.size[0] - logo.size[0]) / 2)
                pasteY = int((bg.size[1] - logo.size[1]) / 2)
                # And finally copy the background and paste in the image
                finalArt = bg.copy()
                finalArt.paste(logo, (pasteX, pasteY), logo)
                # Write out the file
                finalArt.save(f'{IMAGE_DIR}/' + game.app_name + '/FinalArt.png')
                logoCopy = logo.copy()
                logoCopy.putalpha(int(256 * 3 / 4))
                logo.paste(logoCopy, logo)
                uninstalledArt = bg.copy()
                uninstalledArt.paste(logo, (pasteX, pasteY), logo)
                uninstalledArt = uninstalledArt.convert('L')
                uninstalledArt.save(f'{IMAGE_DIR}/' + game.app_name + '/UninstalledArt.png')
            else:
                # We just open up the background and save that as the final image
                if os.path.isfile(f'{IMAGE_DIR}/' + game.app_name + '/DieselGameBoxTall.png'):
                    finalArt = Image.open(f'{IMAGE_DIR}/' + game.app_name + '/DieselGameBoxTall.png')
                    finalArt.save(f'{IMAGE_DIR}/{game.app_name}/FinalArt.png')
                    # And same with the grayscale one
                    uninstalledArt = finalArt.convert('L')
                    uninstalledArt.save(f'{IMAGE_DIR}/{game.app_name}/UninstalledArt.png')
                else:
                    logger.warning(f"File {IMAGE_DIR}/{game.app_name}/DieselGameBoxTall.png dowsn't exist")


if __name__ == '__main__':
    main()

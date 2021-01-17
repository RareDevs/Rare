import logging
import os
import sys

import requests
from PyQt5.QtCore import QTranslator
from PyQt5.QtWidgets import QApplication, QMessageBox
from legendary.core import LegendaryCore

from Rare import style_path, lang_path
from Rare.MainWindow import MainWindow
from Rare.Start.Launch import LaunchDialog
from Rare.Start.Login import LoginWindow
from Rare.utils.RareUtils import get_lang

logging.basicConfig(
    format='[%(name)s] %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("Rare")
core = LegendaryCore()


def main():
    app = QApplication(sys.argv)
    translator = QTranslator()
    lang = get_lang()

    if os.path.exists(lang_path + lang + ".qm"):
        translator.load(lang_path + lang + ".qm")
    else:
        logger.info("Your language is not supported")
    app.installTranslator(translator)

    app.setStyleSheet(open(style_path + "dark.qss").read())

    offline = True

    logger.info("Try if you are logged in")
    try:
        if core.login():
            logger.info("You are logged in")
            offline = False
        else:
            logger.error("Login Failed")
            main()

    except ValueError:
        logger.info("You are not logged in. Open Login Window")
        login_window = LoginWindow(core)
        if not login_window.login():
            return

        # Start Offline mode
    except requests.exceptions.ConnectionError:
        offline = True
        QMessageBox.information(None, "Offline", "You are offline. Launching Rare in offline mode")
        # Launch Offlienmode
    if not offline:
        launch_dialog = LaunchDialog(core)
    mainwindow = MainWindow(core, offline)
# if RareConfig.THEME == "default":
    #   launch_dialog.setStyleSheet(open(style_path).read())

    app.exec_()


if __name__ == '__main__':
    main()

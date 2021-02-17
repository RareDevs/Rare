import logging
import os
import sys

import requests
from PyQt5.QtCore import QTranslator, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMessageBox

from legendary.core import LegendaryCore

from Rare import style_path, lang_path
from Rare.Components.MainWindow import MainWindow

# from Rare.Start.Launch import LaunchDialog
# from Rare.Start.Login import LoginWindow
# from Rare.utils.RareUtils import get_lang
from Rare.utils.Dialogs.Login.LoginDialog import LoginDialog
from Rare.utils.utils import download_images, get_lang

logging.basicConfig(
    format='[%(name)s] %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("Rare")
core = LegendaryCore()


def main():
    app = QApplication(sys.argv)

    # Translator
    translator = QTranslator()
    lang = get_lang()
    if os.path.exists(lang_path + lang + ".qm"):
        translator.load(lang_path + lang + ".qm")
    elif not lang == "en":
        logger.info("Your language is not supported")
    app.installTranslator(translator)
    # Style
    app.setStyleSheet(open(style_path + "RareStyle.qss").read())

    # Offline mode (not completed)
    offline = True
    # Login
    logger.info("Try if you are logged in")
    try:
        if core.login():
            logger.info("You are logged in")
            offline = False
        else:
            logger.error("Login Failed")
            main()

    except ValueError:
        # If not Logged in: Start Login window
        logger.info("You are not logged in. Open Login Window")
        login_window = LoginDialog(core)
        if not login_window.login():
            return

        # Start Offline mode
    except requests.exceptions.ConnectionError:
        offline = True
        QMessageBox.information(None, "Offline", "You are offline. Launching Rare in offline mode")
        # Launch Offlienmode
    if not offline:
        # launch_dialog = LaunchDialog(core)
        # launch_dialog.exec_()
        pass
    # mainwindow = MainWindow(core)
    mainwindow = MainWindow(core)

    app.exec_()


if __name__ == '__main__':
    main()

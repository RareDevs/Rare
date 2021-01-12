import logging
import os
import sys

from PyQt5.QtWidgets import QApplication
from legendary.core import LegendaryCore

from Rare import style_path
from Rare.MainWindow import MainWindow
from Rare.Start.Launch import LaunchDialog
from Rare.Start.Login import LoginWindow
from Rare.utils import RareConfig

logging.basicConfig(
    format='[%(name)s] %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("Rare")
core = LegendaryCore()


def main():
    app = QApplication(sys.argv)
    if RareConfig.THEME == "default":
        app.setStyleSheet(open(style_path).read())
    # app.setStyleSheet(open("Styles/RareStyle.css").read())
    logger.info("Try if you are logged in")
    try:
        if core.login():

            logger.info("You are logged in")
        else:
            logger.error("Login Failed")
            main()

    except ValueError:
        logger.info("You ar not logged in. Open Login Window")
        login_window = LoginWindow(core)
        if not login_window.login():
            return
    launch_dialog = LaunchDialog(core)
    if RareConfig.THEME == "dark":
        launch_dialog.setStyleSheet(open(style_path).read())
    launch_dialog.exec_()
    mainwindow = MainWindow(core)
    app.exec_()


if __name__ == '__main__':
    main()

import logging
import sys

from PyQt5.QtWidgets import QApplication
from legendary.core import LegendaryCore

from Rare.Login import LoginWindow
from Rare.MainWindow import MainWindow

logging.basicConfig(
    format='[%(name)s] %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("Rare")
core = LegendaryCore()


def main():
    app = QApplication(sys.argv)

    logger.info("Try if you are logged in")
    try:
        core.login()
        logger.info("You are logged in")


    except ValueError:
        logger.info("You ar not logged in. Open Login Window")
        login_window = LoginWindow(core)
        if not login_window.login():
            return

    mainwindow = MainWindow(core)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

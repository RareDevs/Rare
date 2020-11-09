import logging
import sys

from PyQt5.QtWidgets import QTabWidget, QMainWindow, QWidget, QApplication

from Rare.Dialogs import LoginDialog
from Rare.TabWidgets import Settings, GameListInstalled, BrowserTab, GameListUninstalled, UpdateList
from Rare.utils import legendaryUtils
from Rare.utils.RareUtils import download_images

logging.basicConfig(
    format='[%(name)s] %(levelname)s: %(message)s',
    level=logging.INFO
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

    if legendaryUtils.core.login():
        logger.info("Login credentials found")

    else:
        logger.info("No login data found")
        dia = LoginDialog()
        code = dia.get_login()
        if code == 1:
            app.closeAllWindows()
            logger.info("Exit login")
            exit(0)
        elif code == 0:
            logger.info("Login successfully")
    download_images()
    window = MainWindow()
    app.exec_()


if __name__ == '__main__':
    main()

import logging
import os
import sys

from PyQt5.QtCore import QSettings, QTranslator
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from Rare import lang_path, style_path
from Rare.Components.Launch.LaunchDialog import LaunchDialog
from Rare.Components.MainWindow import MainWindow
from Rare.utils.utils import get_lang
from custom_legendary.core import LegendaryCore

logging.basicConfig(
    format='[%(name)s] %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("Rare")


class App(QApplication):
    def __init__(self):
        super(App, self).__init__(sys.argv)
        self.core = LegendaryCore()
        self.setApplicationName("Rare")
        self.setOrganizationName("Rare")
        settings = QSettings()

        # Translator
        self.translator = QTranslator()
        lang = settings.value("language", get_lang(), type=str)
        if os.path.exists(lang_path + lang + ".qm"):
            self.translator.load(lang_path + lang + ".qm")
            logger.info("Your language is supported")
        elif not lang == "en":
            logger.info("Your language is not supported")
        self.installTranslator(self.translator)

        # Style
        self.setStyleSheet(open(style_path + "RareStyle.qss").read())
        self.setWindowIcon(QIcon(style_path + "Logo.png"))

        self.launch_dialog = LaunchDialog(self.core)
        self.launch_dialog.start_app.connect(self.start_app)
        self.launch_dialog.show()

    def start_app(self):
        self.mainwindow = MainWindow(self.core)
        self.launch_dialog.close()


def main():
    app = App()
    app.exec_()


if __name__ == '__main__':
    main()

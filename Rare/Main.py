import logging
import os

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


def main():
    core = LegendaryCore()
    app = QApplication([])
    app.setApplicationName("Rare")
    app.setOrganizationName("Rare")
    # app.setQuitOnLastWindowClosed(False)

    settings = QSettings()
    # Translator
    translator = QTranslator()
    lang = settings.value("language", get_lang(), type=str)

    if os.path.exists(lang_path + lang + ".qm"):
        translator.load(lang_path + lang + ".qm")
    elif not lang == "en":
        logger.info("Your language is not supported")
    app.installTranslator(translator)
    # Style
    app.setStyleSheet(open(style_path + "RareStyle.qss").read())
    app.setWindowIcon(QIcon(style_path + "Logo.png"))
    launch_dialog = LaunchDialog(core)
    launch_dialog.exec_()
    mainwindow = MainWindow(core)

    app.exec_()

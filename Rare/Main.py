import logging
import os
import sys

from PyQt5.QtCore import QTranslator, QSettings
from PyQt5.QtWidgets import QApplication

from legendary.core import LegendaryCore

from Rare import style_path, lang_path
from Rare.Components.Launch.LaunchDialog import LaunchDialog
from Rare.Components.MainWindow import MainWindow
from Rare.utils.utils import get_lang

logging.basicConfig(
    format='[%(name)s] %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("Rare")
core = LegendaryCore()


def main():
    app = QApplication(sys.argv)
    settings = QSettings()
    # Translator
    translator = QTranslator()
    lang = settings.value("language",get_lang() , type=str)

    if os.path.exists(lang_path + lang + ".qm"):
        translator.load(lang_path + lang + ".qm")
    elif not lang == "en":
        logger.info("Your language is not supported")
    app.installTranslator(translator)
    # Style
    app.setStyleSheet(open(style_path + "RareStyle.qss").read())


    launch_dialog = LaunchDialog(core)
    launch_dialog.exec_()
    mainwindow = MainWindow(core)

    app.exec_()


if __name__ == '__main__':
    main()

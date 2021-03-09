import logging
import os

from PyQt5.QtCore import QTranslator, QSettings
from PyQt5.QtGui import QIcon
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


if __name__ == '__main__':
    main()

"""
    tray = QSystemTrayIcon()
    tray.setIcon(icon("fa.gamepad", color="white"))
    tray.setVisible(True)
    menu = QMenu()
    option1 = QAction("Geeks for Geeks")
    option1.triggered.connect(lambda: app.exec_())
    option2 = QAction("GFG")
    menu.addAction(option1)
    menu.addAction(option2)
    # To quit the app
    quit = QAction("Quit")
    quit.triggered.connect(app.quit)
    menu.addAction(quit)
    # Adding options to the System Tray
    tray.setContextMenu(menu)"""

import configparser
import logging
import os
import sys
import time

from PyQt5.QtCore import QSettings, QTranslator
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon

from Rare import lang_path, style_path
from Rare.Components.Launch.LaunchDialog import LaunchDialog
from Rare.Components.MainWindow import MainWindow
from Rare.Components.TrayIcon import TrayIcon
from Rare.utils.utils import get_lang
from custom_legendary.core import LegendaryCore

start_time = time.strftime('%y-%m-%d--%H:%M')  # year-month-day-hour-minute
file_name = os.path.expanduser(f"~/.cache/rare/logs/Rare_{start_time}.log")
if not os.path.exists(os.path.dirname(file_name)):
    os.makedirs(os.path.dirname(file_name))

logging.basicConfig(
    format='[%(name)s] %(levelname)s: %(message)s',
    level=logging.INFO,
    filename=file_name,
    filemode="w"
    )
logger = logging.getLogger("Rare")


class App(QApplication):
    def __init__(self):
        super(App, self).__init__(sys.argv)
        # init Legendary
        try:
            self.core = LegendaryCore()
        except configparser.MissingSectionHeaderError as e:
            logger.warning(f"Config is corrupt: {e}")
            if config_path := os.environ.get('XDG_CONFIG_HOME'):
                path = os.path.join(config_path, 'legendary')
            else:
                path = os.path.expanduser('~/.config/legendary')
            with open(os.path.join(path, "config.ini"), "w") as config_file:
                config_file.write("[Legendary]")
            self.core = LegendaryCore()
        if not "Legendary" in self.core.lgd.config.sections():
            self.core.lgd.config.add_section("Legendary")
            self.core.lgd.save_config()

        # set Application name for settings
        self.mainwindow = None
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

        # tray icon

        # launch app
        self.launch_dialog = LaunchDialog(self.core)
        self.launch_dialog.start_app.connect(self.start_app)
        self.launch_dialog.show()

    def start_app(self):
        self.mainwindow = MainWindow(self.core)
        self.tray_icon = TrayIcon(self)
        self.tray_icon.exit_action.triggered.connect(lambda: exit(0))
        self.tray_icon.start_rare.triggered.connect(self.mainwindow.show)
        self.tray_icon.activated.connect(self.tray)
        self.mainwindow.tab_widget.downloadTab.finished.connect(lambda: self.tray_icon.showMessage(
            self.tr("Download finished"), self.tr("Download finished. Game is playable now"),
            QSystemTrayIcon.Information, 4000))
        self.launch_dialog.close()

    def tray(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.mainwindow.show()
            logger.info("Show App")


def start():
    while True:
        app = App()
        exit_code = app.exec_()
        # if not restart
        if exit_code != -133742:
            break
        # restart app
        del app

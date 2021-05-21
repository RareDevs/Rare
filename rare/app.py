import configparser
import logging
import os
import shutil
import sys
import time

from PyQt5.QtCore import QSettings, QTranslator
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QStyleFactory

from custom_legendary.core import LegendaryCore
from rare import lang_path, style_path
from rare.components.dialogs.launch_dialog import LaunchDialog
from rare.components.main_window import MainWindow
from rare.components.tray_icon import TrayIcon
from rare.utils.utils import get_lang, load_color_scheme

start_time = time.strftime('%y-%m-%d--%H:%M')  # year-month-day-hour-minute
file_name = os.path.expanduser(f"~/.cache/rare/logs/Rare_{start_time}.log")
if not os.path.exists(os.path.dirname(file_name)):
    os.makedirs(os.path.dirname(file_name))

logging.basicConfig(
    format='[%(name)s] %(levelname)s: %(message)s',
    level=logging.INFO,
    filename=file_name,
)
logger = logging.getLogger("Rare")


class App(QApplication):
    def __init__(self, args):
        super(App, self).__init__(sys.argv)
        self.args = args  # add some options
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
        if "Legendary" not in self.core.lgd.config.sections():
            self.core.lgd.config.add_section("Legendary")
            self.core.lgd.save_config()

        # workaround if egl sync enabled, but no programdata path
        if self.core.egl_sync_enabled and not os.path.exists(self.core.egl.programdata_path):
            self.core.lgd.config.remove_option("Legendary", "egl-sync")
            self.core.lgd.save_config()

        # set Application name for settings
        self.mainwindow = None
        self.setApplicationName("Rare")
        self.setOrganizationName("Rare")
        settings = QSettings()

        if args.disable_protondb:
            settings.setValue("disable_protondb", True)
        if args.enable_protondb:
            settings.remove("disable_protondb")

        # Translator
        self.translator = QTranslator()
        lang = settings.value("language", get_lang(), type=str)
        if os.path.exists(lang_path + lang + ".qm"):
            self.translator.load(lang_path + lang + ".qm")
            logger.info("Your language is supported: " + lang)
        elif not lang == "en":
            logger.info("Your language is not supported")
        self.installTranslator(self.translator)

        # Style
        self.setStyle(QStyleFactory.create("Fusion"))
        if settings.value("color_scheme", None) is None and settings.value("style_sheet", None) is None:
            settings.setValue("color_scheme", "")
            settings.setValue("style_sheet", "RareStyle")
        if color := settings.value("color_scheme", False):
            settings.setValue("style_sheet", "")
            custom_palette = load_color_scheme(os.path.join(style_path, "colors", color + ".scheme"))
            if custom_palette is not None:
                self.setPalette(custom_palette)
        elif style := settings.value("style_sheet", False):
            settings.setValue("color_scheme", "")
            self.setStyleSheet(open(os.path.join(style_path, "qss", style + ".qss")).read())
        self.setWindowIcon(QIcon(os.path.join(style_path, "Logo.png")))

        # launch app
        self.launch_dialog = LaunchDialog(self.core, args.offline)
        self.launch_dialog.start_app.connect(self.start_app)

        if not args.silent or args.subparser == "launch":
            self.launch_dialog.show()

    def start_app(self, offline=False):
        self.args.offline = offline
        self.mainwindow = MainWindow(self.core, self.args)
        self.launch_dialog.close()
        self.tray_icon = TrayIcon(self)
        self.tray_icon.exit_action.triggered.connect(lambda: exit(0))
        self.tray_icon.start_rare.triggered.connect(self.mainwindow.show)
        self.tray_icon.activated.connect(self.tray)
        if not offline:
            self.mainwindow.tab_widget.downloadTab.finished.connect(lambda update: self.tray_icon.showMessage(
                self.tr("Download finished"), self.tr("Download finished. Game is playable now"),
                QSystemTrayIcon.Information, 4000) if update else None)

        if not self.args.silent:
            self.mainwindow.show()

    def tray(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.mainwindow.show()
            logger.info("Show App")


def start(args):
    while True:
        app = App(args)
        exit_code = app.exec_()
        # if not restart
        if exit_code != -133742:
            break
        # restart app
        del app

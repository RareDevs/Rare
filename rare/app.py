import configparser
import logging
import os
import platform
import sys
import time
import traceback

import qtawesome
from PyQt5.QtCore import QThreadPool, QSettings, QTranslator
from PyQt5.QtGui import QIcon, QPalette
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QStyleFactory, QMessageBox
from requests import HTTPError

import rare.shared as shared
from rare import languages_path, resources_path, cache_dir
from rare.components.dialogs.launch_dialog import LaunchDialog
from rare.components.main_window import MainWindow
from rare.components.tray_icon import TrayIcon
from rare.utils.utils import load_color_scheme

start_time = time.strftime('%y-%m-%d--%H-%M')  # year-month-day-hour-minute
file_name = os.path.join(cache_dir, f"logs/Rare_{start_time}.log")
if not os.path.exists(os.path.dirname(file_name)):
    os.makedirs(os.path.dirname(file_name))

logger = logging.getLogger("Rare")


def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("Error")
    if exc_tb == HTTPError:
        try:
            if shared.core.login():
                return
            else:
                raise ValueError
        except Exception as e:
            logger.fatal(str(e))
            QMessageBox.warning(None, "Error", QApplication.tr("Failed to login"))
            QApplication.exit(1)
            return
    logger.fatal(tb)
    QMessageBox.warning(None, "Error", tb)
    QApplication.exit(1)


class App(QApplication):
    def __init__(self):
        super(App, self).__init__(sys.argv)
        self.args = shared.args  # add some options
        # init Legendary
        try:
            self.core = shared.init_legendary()
        except configparser.MissingSectionHeaderError as e:
            logger.warning(f"Config is corrupt: {e}")
            if config_path := os.environ.get('XDG_CONFIG_HOME'):
                path = os.path.join(config_path, 'legendary')
            else:
                path = os.path.expanduser('~/.config/legendary')
            with open(os.path.join(path, "config.ini"), "w") as config_file:
                config_file.write("[Legendary]")
            self.core = shared.init_legendary()
        if "Legendary" not in self.core.lgd.config.sections():
            self.core.lgd.config.add_section("Legendary")
            self.core.lgd.save_config()

        # workaround if egl sync enabled, but no programdata_path
        # programdata_path might be unset if logging in through the browser
        if self.core.egl_sync_enabled:
            if self.core.egl.programdata_path is None:
                self.core.lgd.config.remove_option("Legendary", "egl_sync")
                self.core.lgd.save_config()
            else:
                if not os.path.exists(self.core.egl.programdata_path):
                    self.core.lgd.config.remove_option("Legendary", "egl_sync")
                    self.core.lgd.save_config()

        # set Application name for settings
        self.mainwindow = None
        self.tray_icon = None
        self.launch_dialog = None
        self.setApplicationName("Rare")
        self.setOrganizationName("Rare")
        self.settings = QSettings()

        self.signals = shared.init_signals()

        self.signals.exit_app.connect(self.exit)
        self.signals.send_notification.connect(
            lambda title:
            self.tray_icon.showMessage(
                self.tr("Download finished"),
                self.tr("Download finished. {} is playable now").format(title),
                QSystemTrayIcon.Information, 4000)
            if self.settings.value("notification", True, bool) else None)

        # Translator
        self.translator = QTranslator()
        lang = self.settings.value("language", self.core.language_code, type=str)
        if os.path.exists(p := os.path.join(languages_path, lang + ".qm")):
            self.translator.load(p)
            logger.info("Your language is supported: " + lang)
        elif not lang == "en":
            logger.info("Your language is not supported")
        self.installTranslator(self.translator)

        # Style
        if self.settings.value("color_scheme", None) is None and self.settings.value("style_sheet", None) is None:
            self.settings.setValue("color_scheme", "")
            self.settings.setValue("style_sheet", "RareStyle")

        if color := self.settings.value("color_scheme", False):
            self.setStyle(QStyleFactory.create("Fusion"))
            self.settings.setValue("style_sheet", "")
            custom_palette = load_color_scheme(os.path.join(resources_path, "colors", color + ".scheme"))
            if custom_palette is not None:
                self.setPalette(custom_palette)
                qtawesome.set_defaults(color=custom_palette.color(QPalette.Text))
        elif style := self.settings.value("style_sheet", False):
            self.setStyle(QStyleFactory.create("Fusion"))
            self.settings.setValue("color_scheme", "")
            stylesheet = open(os.path.join(resources_path, "stylesheets", style, "stylesheet.qss")).read()
            style_resource_path = os.path.join(resources_path, "stylesheets", style, "")
            if platform.system() == "Windows":
                style_resource_path = style_resource_path.replace('\\', '/')
            self.setStyleSheet(stylesheet.replace("@path@", style_resource_path))
            qtawesome.set_defaults(color="white")
        self.setWindowIcon(QIcon(os.path.join(resources_path, "images", "Rare.png")))

        # launch app
        self.launch_dialog = LaunchDialog()
        self.launch_dialog.quit_app.connect(self.launch_dialog.close)
        self.launch_dialog.quit_app.connect(lambda ec: exit(ec))
        self.launch_dialog.start_app.connect(self.start_app)
        self.launch_dialog.start_app.connect(self.launch_dialog.close)

        if not self.args.silent or self.args.subparser == "launch":
            self.launch_dialog.login()

    def start_app(self):
        self.mainwindow = MainWindow()
        self.launch_dialog.close()
        self.tray_icon = TrayIcon(self)
        self.tray_icon.exit_action.triggered.connect(self.exit_app)
        self.tray_icon.start_rare.triggered.connect(self.mainwindow.show)
        self.tray_icon.activated.connect(self.tray)

        if not self.args.silent:
            self.mainwindow.show()

    def tray(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.mainwindow.show()
            logger.info("Show App")

    def exit_app(self, exit_code=0):
        self.mainwindow.hide()
        threadpool = QThreadPool.globalInstance()
        threadpool.waitForDone()
        if self.mainwindow is not None:
            self.mainwindow.close()
        if self.tray_icon is not None:
            self.tray_icon.deleteLater()
        self.processEvents()
        self.exit(exit_code)


def start(args):
    # set excepthook to show dialog with exception
    sys.excepthook = excepthook
    shared.init_args(args)

    # configure logging
    if args.debug:
        logging.basicConfig(format='[%(name)s] %(levelname)s: %(message)s', level=logging.DEBUG)
        logging.getLogger().setLevel(level=logging.DEBUG)
        # keep requests, asyncio and pillow quiet
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger("PIL.TiffImagePlugin").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)
    else:
        logging.basicConfig(
            format='[%(name)s] %(levelname)s: %(message)s',
            level=logging.INFO,
            filename=file_name,
        )

    while True:
        app = App()
        exit_code = app.exec_()
        # if not restart
        # restart app
        del app
        if exit_code != -133742:
            break

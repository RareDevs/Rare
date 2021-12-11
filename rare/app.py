import configparser
import logging
import os
import platform
import sys
import time
import traceback

from PyQt5.QtCore import QThreadPool, QSettings, QTranslator
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMessageBox
from requests import HTTPError

import legendary
# noinspection PyUnresolvedReferences
import rare.resources.resources
import rare.shared as shared
from rare import cache_dir, resources_path
from rare.components.dialogs.launch_dialog import LaunchDialog
from rare.components.main_window import MainWindow
from rare.components.tray_icon import TrayIcon
from rare.utils.utils import set_color_pallete, set_style_sheet

start_time = time.strftime('%y-%m-%d--%H-%M')  # year-month-day-hour-minute
file_name = os.path.join(cache_dir, "logs", f"Rare_{start_time}.log")
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

        if os.path.isfile(f := os.path.join(resources_path, "languages", f"{lang}.qm")):
            self.translator.load(f)
            logger.info("Your language is supported: " + lang)
        elif not lang == "en":
            logger.info("Your language is not supported")
        self.installTranslator(self.translator)

        # translator for qt stuff
        if os.path.isfile(f := os.path.join(resources_path, f"qt_{lang}.qm")):
            self.qt_translator = QTranslator()
            self.qt_translator.load(f)
            self.installTranslator(self.qt_translator)

        # Style
        # lk: this is a bit silly but serves well until we have a class
        # lk: store the default qt style name from the system on startup as a property for later reference
        self.setProperty('rareDefaultQtStyle', self.style().objectName())

        if self.settings.value("color_scheme", None) is None and self.settings.value("style_sheet", None) is None:
            self.settings.setValue("color_scheme", "")
            self.settings.setValue("style_sheet", "RareStyle")

        if color_scheme := self.settings.value("color_scheme", False):
            self.settings.setValue("style_sheet", "")
            set_color_pallete(color_scheme)
        elif style_sheet := self.settings.value("style_sheet", False):
            self.settings.setValue("color_scheme", "")
            set_style_sheet(style_sheet)
        self.setWindowIcon(QIcon(":/images/Rare.png"))

        # launch app
        self.launch_dialog = LaunchDialog()
        self.launch_dialog.quit_app.connect(self.launch_dialog.close)
        self.launch_dialog.quit_app.connect(lambda ec: exit(ec))
        self.launch_dialog.start_app.connect(self.start_app)
        self.launch_dialog.start_app.connect(self.launch_dialog.close)

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

        if shared.args.subparser == "launch":
            if shared.args.app_name in [i.app_name for i in self.core.get_installed_list()]:
                logger.info("Launching " + self.core.get_installed_game(shared.args.app_name).title)
                self.mainwindow.tab_widget.games_tab.game_utils.prepare_launch(shared.args.app_name)
            else:
                logger.error(
                    f"Could not find {shared.args.app_name} in Games or it is not installed")
                QMessageBox.warning(self.mainwindow, "Warning",
                                    self.tr(
                                        "Could not find {} in installed games. Did you modify the shortcut? ").format(
                                        shared.args.app_name))

        if shared.args.test_start:
            self.exit_app(0)

    def tray(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.mainwindow.show()
            logger.info("Show App")

    def exit_app(self, exit_code=0):
        # FIXME: Fix this with the downlaod tab redesign
        if self.mainwindow is not None:
            if self.mainwindow.tab_widget.downloadTab.active_game is not None:
                question = QMessageBox.question(
                    self.mainwindow,
                    self.tr("Close"),
                    self.tr("There is a download active. Do you really want to exit app?"),
                    QMessageBox.Yes, QMessageBox.No)
                if question == QMessageBox.No:
                    return
                else:
                    self.mainwindow.tab_widget.downloadTab.stop_download()
        # FIXME: End of FIXME
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
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        logger.info(f"Launching Rare version {rare.__version__} Codename: {rare.code_name}\n"
                    f"Using Legendary {legendary.__version__} Codename: {legendary.__codename__} as backend\n"
                    f"Operating System: {platform.system()}, Python version: {platform.python_version()}\n"
                    f"Running {sys.executable} {' '.join(sys.argv)}")
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

import configparser
import logging
import os
import platform
import shutil
import sys
import time
import traceback
from argparse import Namespace
from datetime import datetime
from typing import Optional

import legendary
import requests.exceptions
from PyQt5.QtCore import QThreadPool, QTimer
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMessageBox
from requests import HTTPError

import rare
from rare.components.dialogs.launch_dialog import LaunchDialog
from rare.components.main_window import MainWindow
from rare.components.tray_icon import TrayIcon
from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton, ArgumentsSingleton
from rare.shared.image_manager import ImageManagerSingleton
from rare.utils import legendary_utils, config_helper
from rare.utils.paths import cache_dir, tmp_dir
from rare.widgets.rare_app import RareApp

start_time = time.strftime("%y-%m-%d--%H-%M")  # year-month-day-hour-minute
file_name = os.path.join(cache_dir, "logs", f"Rare_{start_time}.log")
if not os.path.exists(os.path.dirname(file_name)):
    os.makedirs(os.path.dirname(file_name))

logger = logging.getLogger("Rare")


def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("Error")
    if exc_tb == HTTPError:
        try:
            if LegendaryCoreSingleton().login():
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


class App(RareApp):
    mainwindow: Optional[MainWindow] = None
    tray_icon: Optional[QSystemTrayIcon] = None

    def __init__(self, args: Namespace):
        super(App, self).__init__()
        self.args = ArgumentsSingleton(args)  # add some options
        self.window_launched = False

        # init Legendary
        try:
            self.core = LegendaryCoreSingleton(init=True)
        except configparser.MissingSectionHeaderError as e:
            logger.warning(f"Config is corrupt: {e}")
            if config_path := os.environ.get("XDG_CONFIG_HOME"):
                path = os.path.join(config_path, "legendary")
            else:
                path = os.path.expanduser("~/.config/legendary")
            with open(os.path.join(path, "config.ini"), "w") as config_file:
                config_file.write("[Legendary]")
            self.core = LegendaryCoreSingleton(init=True)
        if "Legendary" not in self.core.lgd.config.sections():
            self.core.lgd.config.add_section("Legendary")
            self.core.lgd.save_config()

        lang = self.settings.value("language", self.core.language_code, type=str)
        self.load_translator(lang)

        config_helper.init_config_handler(self.core)

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
        self.launch_dialog = None

        self.signals = GlobalSignalsSingleton(init=True)
        self.image_manager = ImageManagerSingleton(init=True)

        self.signals.exit_app.connect(self.exit_app)
        self.signals.send_notification.connect(
            lambda title: self.tray_icon.showMessage(
                self.tr("Download finished"),
                self.tr("Download finished. {} is playable now").format(title),
                QSystemTrayIcon.Information,
                4000,
            )
            if self.settings.value("notification", True, bool)
            else None
        )

        # launch app
        self.launch_dialog = LaunchDialog()
        self.launch_dialog.quit_app.connect(self.launch_dialog.close)
        self.launch_dialog.quit_app.connect(lambda ec: exit(ec))
        self.launch_dialog.start_app.connect(self.start_app)
        self.launch_dialog.start_app.connect(self.launch_dialog.close)

        self.launch_dialog.login()

        dt_exp = datetime.fromisoformat(self.core.lgd.userdata['expires_at'][:-1])
        dt_now = datetime.utcnow()
        td = abs(dt_exp - dt_now)
        self.timer = QTimer()
        self.timer.timeout.connect(self.re_login)
        self.timer.start(int(td.total_seconds() - 60) * 1000)

    def re_login(self):
        logger.info("Session expires shortly. Renew session")
        try:
            self.core.login()
        except requests.exceptions.ConnectionError:
            self.timer.start(3000)  # try again if no connection
            return
        dt_exp = datetime.fromisoformat(self.core.lgd.userdata['expires_at'][:-1])
        dt_now = datetime.utcnow()
        td = abs(dt_exp - dt_now)
        self.timer.start(int(td.total_seconds() - 60) * 1000)

    def show_mainwindow(self):
        if self.window_launched:
            self.mainwindow.show()
        else:
            self.mainwindow.show_window_centered()

    def start_app(self):
        for igame in self.core.get_installed_list():
            if not os.path.exists(igame.install_path):
                legendary_utils.uninstall(igame.app_name, self.core)
                logger.info(f"Uninstalled {igame.title}, because no game files exist")
                continue
            if not os.path.exists(os.path.join(igame.install_path, igame.executable.replace("\\", "/").lstrip("/"))):
                igame.needs_verification = True
                self.core.lgd.set_installed_game(igame.app_name, igame)
                logger.info(f"{igame.title} needs verification")

        self.mainwindow = MainWindow()
        self.launch_dialog.close()
        self.tray_icon = TrayIcon(self)
        self.tray_icon.exit_action.triggered.connect(self.exit_app)
        self.tray_icon.start_rare.triggered.connect(self.show_mainwindow)
        self.tray_icon.activated.connect(
            lambda r: self.show_mainwindow()
            if r == QSystemTrayIcon.DoubleClick
            else None
        )

        if not self.args.silent:
            self.mainwindow.show_window_centered()
            self.window_launched = True

        if self.args.subparser == "launch":
            if self.args.app_name in [
                i.app_name for i in self.core.get_installed_list()
            ]:
                logger.info(
                    f"Launching {self.core.get_installed_game(self.args.app_name).title}"
                )
                self.mainwindow.tab_widget.games_tab.game_utils.prepare_launch(
                    self.args.app_name
                )
            else:
                logger.error(
                    f"Could not find {self.args.app_name} in Games or it is not installed"
                )
                QMessageBox.warning(
                    self.mainwindow,
                    "Warning",
                    self.tr(
                        "Could not find {} in installed games. Did you modify the shortcut? "
                    ).format(self.args.app_name),
                )

        if self.args.test_start:
            self.exit_app(0)

    def tray(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.mainwindow.show()
            logger.info("Show App")

    def exit_app(self, exit_code=0):
        # FIXME: Fix this with the downlaod tab redesign
        if self.mainwindow is not None:
            if not self.args.offline and self.mainwindow.tab_widget.downloadTab.is_download_active:
                question = QMessageBox.question(
                    self.mainwindow,
                    self.tr("Close"),
                    self.tr(
                        "There is a download active. Do you really want to exit app?"
                    ),
                    QMessageBox.Yes,
                    QMessageBox.No,
                )
                if question == QMessageBox.No:
                    return
                else:
                    # clear queue
                    self.mainwindow.tab_widget.downloadTab.queue_widget.update_queue([])
                    self.mainwindow.tab_widget.downloadTab.stop_download()
        # FIXME: End of FIXME
        self.mainwindow.timer.stop()
        self.mainwindow.hide()
        threadpool = QThreadPool.globalInstance()
        threadpool.waitForDone()
        if self.mainwindow is not None:
            self.mainwindow.close()
        if self.tray_icon is not None:
            self.tray_icon.deleteLater()
        self.processEvents()
        shutil.rmtree(tmp_dir)
        os.makedirs(tmp_dir)

        self.exit(exit_code)


def start(args):
    # set excepthook to show dialog with exception
    sys.excepthook = excepthook

    # configure logging
    if args.debug:
        logging.basicConfig(
            format="[%(name)s] %(levelname)s: %(message)s", level=logging.DEBUG
        )
        logging.getLogger().setLevel(level=logging.DEBUG)
        # keep requests, asyncio and pillow quiet
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        logger.info(
            f"Launching Rare version {rare.__version__} Codename: {rare.code_name}\n"
            f"Using Legendary {legendary.__version__} Codename: {legendary.__codename__} as backend\n"
            f"Operating System: {platform.system()}, Python version: {platform.python_version()}\n"
            f"Running {sys.executable} {' '.join(sys.argv)}"
        )
    else:
        logging.basicConfig(
            format="[%(name)s] %(levelname)s: %(message)s",
            level=logging.INFO,
            filename=file_name,
        )
        logger.info(f"Launching Rare version {rare.__version__}")
        logger.info(f"Operating System: {platform.system()}")

    while True:
        app = App(args)
        exit_code = app.exec_()
        # if not restart
        # restart app
        del app
        if exit_code != -133742:
            break

import logging
import os
import shutil
import sys
import time
import traceback
from argparse import Namespace
from datetime import datetime
from typing import Optional

import requests.exceptions
from PyQt5.QtCore import QThreadPool, QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox
from requests import HTTPError

from rare.components.dialogs.launch_dialog import LaunchDialog
from rare.components.main_window import MainWindow
from rare.shared import (
    LegendaryCoreSingleton,
    GlobalSignalsSingleton,
    ArgumentsSingleton,
)
from rare.shared.rare_core import RareCore
from rare.utils import legendary_utils, config_helper, paths
from rare.widgets.rare_app import RareApp

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
    def __init__(self, args: Namespace):
        log_file = "Rare_{0}.log"
        super(App, self).__init__(args, log_file)
        self.rare_core = RareCore(args=args)
        self.args = ArgumentsSingleton()
        self.signals = GlobalSignalsSingleton()
        self.core = LegendaryCoreSingleton()

        config_helper.init_config_handler(self.core)

        lang = self.settings.value("language", self.core.language_code, type=str)
        self.load_translator(lang)

        # set Application name for settings
        self.mainwindow: Optional[MainWindow] = None
        self.launch_dialog: Optional[LaunchDialog] = None
        self.timer = QTimer()

        # launch app
        self.launch_dialog = LaunchDialog(parent=None)
        self.launch_dialog.quit_app.connect(self.launch_dialog.close)
        self.launch_dialog.quit_app.connect(lambda ec: exit(ec))
        self.launch_dialog.start_app.connect(self.start_app)
        self.launch_dialog.start_app.connect(self.launch_dialog.close)

        self.launch_dialog.login()

        dt_exp = datetime.fromisoformat(self.core.lgd.userdata['expires_at'][:-1])
        dt_now = datetime.utcnow()
        td = abs(dt_exp - dt_now)
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

    def start_app(self):
        for igame in self.core.get_installed_list():
            if not os.path.exists(igame.install_path):
                # lk; since install_path is lost anyway, set keep_files to True
                # lk: to avoid spamming the log with "file not found" errors
                legendary_utils.uninstall_game(self.core, igame.app_name, keep_files=True)
                logger.info(f"Uninstalled {igame.title}, because no game files exist")
                continue
            # lk: games that don't have an override and can't find their executable due to case sensitivity
            # lk: will still erroneously require verification. This might need to be removed completely
            # lk: or be decoupled from the verification requirement
            if override_exe := self.core.lgd.config.get(igame.app_name, "override_exe", fallback=""):
                igame_executable = override_exe
            else:
                igame_executable = igame.executable
            if not os.path.exists(os.path.join(igame.install_path, igame_executable.replace("\\", "/").lstrip("/"))):
                igame.needs_verification = True
                self.core.lgd.set_installed_game(igame.app_name, igame)
                logger.info(f"{igame.title} needs verification")

        self.mainwindow = MainWindow()
        self.mainwindow.exit_app.connect(self.exit_app)

        if not self.args.silent:
            self.mainwindow.show()

        if self.args.test_start:
            self.exit_app(0)

    def exit_app(self, exit_code=0):
        threadpool = QThreadPool.globalInstance()
        threadpool.waitForDone()
        if self.timer is not None:
            self.timer.stop()
            self.timer.deleteLater()
            self.timer = None
        if self.mainwindow is not None:
            self.mainwindow.close()
            self.mainwindow = None
        self.rare_core.deleteLater()
        del self.rare_core
        self.processEvents()
        shutil.rmtree(paths.tmp_dir())
        os.makedirs(paths.tmp_dir())

        self.exit(exit_code)


def start(args):
    # set excepthook to show dialog with exception
    sys.excepthook = excepthook

    while True:
        app = App(args)
        exit_code = app.exec_()
        # if not restart
        # restart app
        del app
        if exit_code != -133742:
            break



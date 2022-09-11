import logging
import os
import shutil
import sys
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
from rare.utils import config_helper, paths
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
        self.main_window: Optional[MainWindow] = None
        self.launch_dialog: Optional[LaunchDialog] = None
        self.timer: Optional[QTimer] = None

        # launch app
        self.launch_dialog = LaunchDialog(parent=None)
        self.launch_dialog.quit_app.connect(self.launch_dialog.close)
        self.launch_dialog.quit_app.connect(lambda x: sys.exit(x))
        self.launch_dialog.start_app.connect(self.start_app)
        self.launch_dialog.start_app.connect(self.launch_dialog.close)

        self.launch_dialog.login()

    def poke_timer(self):
        dt_exp = datetime.fromisoformat(self.core.lgd.userdata['expires_at'][:-1])
        dt_now = datetime.utcnow()
        td = abs(dt_exp - dt_now)
        self.timer.start(int(td.total_seconds() - 60) * 1000)

    def re_login(self):
        logger.info("Session expires shortly. Renew session")
        try:
            self.core.login()
        except requests.exceptions.ConnectionError:
            self.timer.start(3000)  # try again if no connection
            return
        self.poke_timer()

    def start_app(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.re_login)
        self.poke_timer()

        self.main_window = MainWindow()
        self.main_window.exit_app.connect(self.exit_app)

        if not self.args.silent:
            self.main_window.show()

        if self.args.test_start:
            self.exit_app(0)

    def exit_app(self, exit_code=0):
        threadpool = QThreadPool.globalInstance()
        threadpool.waitForDone()
        if self.timer is not None:
            self.timer.stop()
            self.timer.deleteLater()
            self.timer = None
        if self.main_window is not None:
            self.main_window.close()
            self.main_window = None
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



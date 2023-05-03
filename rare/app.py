import logging
import os
import shutil
import sys
import traceback
from argparse import Namespace
from datetime import datetime, timezone
from typing import Optional

import requests.exceptions
from PyQt5.QtCore import QThreadPool, QTimer, pyqtSlot, Qt
from PyQt5.QtWidgets import QApplication, QMessageBox
from requests import HTTPError

from rare.components.dialogs.launch_dialog import LaunchDialog
from rare.components.main_window import MainWindow
from rare.shared import RareCore
from rare.utils import config_helper, paths
from rare.widgets.rare_app import RareApp, RareAppException

logger = logging.getLogger("Rare")


class RareException(RareAppException):
    def __init__(self, parent=None):
        super(RareException, self).__init__(parent=parent)

    def _handler(self, exc_type, exc_value, exc_tb) -> bool:
        if exc_type == HTTPError:
            try:
                if RareCore.instance() is not None:
                    if RareCore.instance().core().login():
                        return True
                raise ValueError
            except Exception as e:
                logger.fatal(str(e))
                QMessageBox.warning(None, "Error", self.tr("Failed to login"))
                QApplication.exit(1)
        return False


class Rare(RareApp):
    def __init__(self, args: Namespace):
        log_file = "Rare_{0}.log"
        super(Rare, self).__init__(args, log_file)
        self._hook.deleteLater()
        self._hook = RareException(self)
        self.rcore = RareCore(args=args)
        self.args = RareCore.instance().args()
        self.signals = RareCore.instance().signals()
        self.core = RareCore.instance().core()

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
        dt_exp = datetime.fromisoformat(self.core.lgd.userdata['expires_at'][:-1]).replace(tzinfo=timezone.utc)
        dt_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        td = abs(dt_exp - dt_now)
        self.timer.start(int(td.total_seconds() - 60) * 1000)
        logger.info(f"Renewed session expires at {self.core.lgd.userdata['expires_at']}")

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
        self.main_window.exit_app.connect(self.on_exit_app)

        if not self.args.silent:
            self.main_window.show()

        if self.args.test_start:
            self.main_window.close()
            self.main_window = None
            self.on_exit_app(0)

    @pyqtSlot()
    @pyqtSlot(int)
    def on_exit_app(self, exit_code=0):
        threadpool = QThreadPool.globalInstance()
        threadpool.waitForDone()
        if self.timer is not None:
            self.timer.stop()
            self.timer.deleteLater()
            self.timer = None
        self.rcore.deleteLater()
        del self.rcore
        self.processEvents()
        shutil.rmtree(paths.tmp_dir())
        os.makedirs(paths.tmp_dir())

        self.exit(exit_code)


def start(args):
    while True:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        app = Rare(args)
        exit_code = app.exec_()
        # if not restart
        # restart app
        del app
        if exit_code != -133742:
            break

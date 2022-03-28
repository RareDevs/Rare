import os
import platform
from logging import getLogger

from PyQt5.QtCore import Qt, pyqtSignal, QRunnable, QObject, QThreadPool, QSettings
from PyQt5.QtWidgets import QDialog, QApplication
from legendary.core import LegendaryCore
from requests.exceptions import ConnectionError, HTTPError

from rare.shared import LegendaryCoreSingleton, ArgumentsSingleton, ApiResultsSingleton
from rare.components.dialogs.login import LoginDialog
from rare.ui.components.dialogs.launch_dialog import Ui_LaunchDialog
from rare.utils.models import ApiResults
from rare.utils.paths import image_dir
from rare.utils.utils import download_images, CloudWorker

logger = getLogger("Login")


class LaunchDialogSignals(QObject):
    image_progress = pyqtSignal(int)
    result = pyqtSignal(object, str)


class ImageWorker(QRunnable):
    def __init__(self, core: LegendaryCore):
        super(ImageWorker, self).__init__()
        self.signals = LaunchDialogSignals()
        self.setAutoDelete(True)
        self.core = core

    def run(self):
        download_images(self.signals.image_progress, self.signals.result, self.core)
        self.signals.image_progress.emit(100)


class ApiRequestWorker(QRunnable):
    def __init__(self):
        super(ApiRequestWorker, self).__init__()
        self.signals = LaunchDialogSignals()
        self.setAutoDelete(True)
        self.core = LegendaryCoreSingleton()
        self.settings = QSettings()

    def run(self) -> None:
        if self.settings.value("mac_meta", platform.system() == "Darwin", bool):
            try:
                result = self.core.get_game_and_dlc_list(True, "Mac")
            except HTTPError:
                result = [], {}
            self.signals.result.emit(result, "mac")
        else:
            self.signals.result.emit(([], {}), "mac")

        if self.settings.value("win32_meta", False, bool):
            try:
                result = self.core.get_game_and_dlc_list(True, "Win32")
            except HTTPError:
                result = [], {}
        else:
            result = [], {}
        self.signals.result.emit(result, "32bit")


class LaunchDialog(QDialog, Ui_LaunchDialog):
    quit_app = pyqtSignal(int)
    start_app = pyqtSignal()
    finished = 0

    def __init__(self, parent=None):
        super(LaunchDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setWindowModality(Qt.WindowModal)

        self.core = LegendaryCoreSingleton()
        self.args = ArgumentsSingleton()
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(2)
        self.api_results = ApiResults()

    def login(self):
        do_launch = True
        try:
            if self.args.offline:
                pass
            else:
                QApplication.processEvents()
                if self.core.login():
                    logger.info("You are logged in")
                else:
                    raise ValueError("You are not logged in. Open Login Window")
        except ValueError as e:
            logger.info(str(e))
            do_launch = LoginDialog(core=self.core, parent=self).login()
        except ConnectionError as e:
            logger.warning(e)
            self.args.offline = True
        finally:
            if do_launch:
                if not self.args.silent:
                    self.show()
                self.launch()
            else:
                self.quit_app.emit(0)

    def launch(self):
        # self.core = core
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)

        if not self.args.offline:
            self.image_info.setText(self.tr("Downloading Images"))
            image_worker = ImageWorker(self.core)
            image_worker.signals.image_progress.connect(self.update_image_progbar)
            image_worker.signals.result.connect(self.handle_api_worker_result)
            self.thread_pool.start(image_worker)

            # gamelist and no_asset games are from Image worker
            worker = ApiRequestWorker()
            worker.signals.result.connect(self.handle_api_worker_result)
            self.thread_pool.start(worker)

            # cloud save from another worker, because it is used in cloud_save_utils too
            cloud_worker = CloudWorker()
            cloud_worker.signals.result_ready.connect(
                lambda x: self.handle_api_worker_result(x, "saves")
            )
            self.thread_pool.start(cloud_worker)

        else:
            self.finished = 2
            if self.core.lgd.assets:
                (
                    self.api_results.game_list,
                    self.api_results.dlcs,
                ) = self.core.get_game_and_dlc_list(False)
                self.api_results.bit32_games = list(
                    map(lambda i: i.app_name, self.core.get_game_list(False, "Win32"))
                )
                self.api_results.mac_games = list(
                    map(lambda i: i.app_name, self.core.get_game_list(False, "Mac"))
                )
            else:
                logger.warning("No assets found. Falling back to empty game lists")
                self.api_results.game_list, self.api_results.dlcs = [], {}
                self.api_results.mac_games = self.api_results.bit32_games = []
            self.finish()

    def handle_api_worker_result(self, result, text):
        logger.debug(f"Api Request got from {text}")
        if text == "gamelist":
            if result:
                self.api_results.game_list, self.api_results.dlcs = result
            else:
                (
                    self.api_results.game_list,
                    self.api_results.dlcs,
                ) = self.core.get_game_and_dlc_list(False)
        elif text == "32bit":
            self.api_results.bit32_games = (
                [i.app_name for i in result[0]] if result else []
            )
        elif text == "mac":
            self.api_results.mac_games = (
                [i.app_name for i in result[0]] if result else []
            )

        elif text == "no_assets":
            self.api_results.no_asset_games = result if result else []

        elif text == "saves":
            self.api_results.saves = result

        if self.api_results:
            self.finish()

    def update_image_progbar(self, i: int):
        self.image_prog_bar.setValue(i)
        if i == 100:
            self.finish()

    def finish(self):
        if self.finished == 1:
            logger.info("App starting")
            self.image_info.setText(self.tr("Starting..."))
            ApiResultsSingleton(self.api_results)
            self.start_app.emit()
        else:
            self.finished += 1

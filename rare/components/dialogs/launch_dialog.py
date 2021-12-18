import os
import platform
from logging import getLogger

from PyQt5.QtCore import Qt, pyqtSignal, QRunnable, QObject, QThreadPool
from PyQt5.QtWidgets import QDialog
from requests.exceptions import ConnectionError, HTTPError

from legendary.core import LegendaryCore
from legendary.models.game import GameAsset
from rare import image_dir, shared
from rare.components.dialogs.login import LoginDialog
from rare.ui.components.dialogs.launch_dialog import Ui_LaunchDialog
from rare.utils.models import ApiResults
from rare.utils.utils import download_images, CloudWorker

logger = getLogger("Login")


class ApiSignals(QObject):
    image_progress = pyqtSignal(int)
    result = pyqtSignal(object, str)


class ImageWorker(QRunnable):
    def __init__(self, core: LegendaryCore):
        super(ImageWorker, self).__init__()
        self.core = core
        self.signal = ApiSignals()
        self.setAutoDelete(True)

    def run(self):
        download_images(self.signal.image_progress, self.signal.result, self.core)
        self.signal.image_progress.emit(100)


class ApiRequestWorker(QRunnable):
    def __init__(self):
        super(ApiRequestWorker, self).__init__()
        self.signals = ApiSignals()
        self.setAutoDelete(True)

    def run(self) -> None:
        try:
            result = shared.core.get_game_and_dlc_list(True, "Mac")
        except HTTPError():
            result = [], {}
        self.signals.result.emit(result, "mac")

        try:
            result = shared.core.get_game_and_dlc_list(True, "Win32")
        except HTTPError():
            result = [], {}
        self.signals.result.emit(result, "32bit")


class AssetWorker(QRunnable):
    def __init__(self):
        super(AssetWorker, self).__init__()
        self.signals = ApiSignals()
        self.setAutoDelete(True)
        self.assets = dict()

    def run(self) -> None:
        platforms = shared.core.get_installed_platforms()
        platforms.add("Windows")
        if platform.system() == "Darwin":
            platforms.add("Mac")
        for p in platforms:
            self.assets.update({p: self.get_asset(p)})
        self.signals.result.emit(self.assets, "assets")

    @staticmethod
    def get_asset(p):
        if not shared.core.egs.user:
            return []
        assets = [
            GameAsset.from_egs_json(a) for a in
            shared.core.egs.get_game_assets(platform=p)
        ]

        return assets


class LaunchDialog(QDialog, Ui_LaunchDialog):
    quit_app = pyqtSignal(int)
    start_app = pyqtSignal()
    finished = 0

    def __init__(self, parent=None):
        super(LaunchDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.core = shared.core
        self.offline = shared.args.offline
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(2)
        self.api_results = ApiResults()

    def login(self):
        do_launch = True
        try:
            if self.offline:
                pass
            else:
                if self.core.login():
                    logger.info("You are logged in")
                else:
                    raise ValueError("You are not logged in. Open Login Window")
        except ValueError as e:
            logger.info(str(e))
            do_launch = LoginDialog(core=self.core, parent=self).login()
        except ConnectionError as e:
            logger.warning(e)
            self.offline = True
        finally:
            if do_launch:
                if not shared.args.silent:
                    self.show()
                self.launch()
            else:
                self.quit_app.emit(0)

    def launch(self):
        # self.core = core
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)

        if not self.offline:
            self.image_info.setText(self.tr("Downloading Images"))
            image_worker = ImageWorker(self.core)
            image_worker.signal.image_progress.connect(self.update_image_progbar)
            image_worker.signal.result.connect(self.handle_api_worker_result)
            self.thread_pool.start(image_worker)

            # gamelist and no_asset games are from Image worker
            worker = ApiRequestWorker()
            worker.signals.result.connect(self.handle_api_worker_result)
            self.thread_pool.start(worker)

            asset_worker = AssetWorker()
            asset_worker.signals.result.connect(self.handle_api_worker_result)
            self.thread_pool.start(asset_worker)

            # cloud save from another worker, because it is used in cloud_save_utils too
            cloud_worker = CloudWorker()
            cloud_worker.signals.result_ready.connect(lambda x: self.handle_api_worker_result(x, "saves"))
            self.thread_pool.start(cloud_worker)

        else:
            self.finished = 2
            if self.core.lgd.assets:
                self.api_results.game_list, self.api_results.dlcs = self.core.get_game_and_dlc_list(False)
                self.api_results.bit32_games = list(map(lambda i: i.app_name, self.core.get_game_list(False, "Win32")))
                self.api_results.mac_games = list(map(lambda i: i.app_name, self.core.get_game_list(False, "Mac")))
            else:
                logger.warning("No assets found. Falling back to empty game lists")
                self.api_results.game_list, self.api_results.dlcs = [], {}
                self.api_results.mac_games = self.api_results.bit32_games = []
            self.finish()

    def handle_api_worker_result(self, result, text):
        logger.debug("Api Request got from " + text)
        if text == "gamelist":
            if result:
                self.api_results.game_list, self.api_results.dlcs = result
            else:
                self.api_results.game_list, self.api_results.dlcs = self.core.get_game_and_dlc_list(False)
        elif text == "32bit":
            self.api_results.bit32_games = [i.app_name for i in result[0]] if result else []
        elif text == "mac":
            self.api_results.mac_games = [i.app_name for i in result[0]] if result else []

        elif text == "no_assets":
            self.api_results.no_asset_games = result if result else []

        elif text == "saves":
            self.api_results.saves = result
        elif text == "assets":
            self.core.lgd.assets = result
            self.finish()
            return

        if self.api_results:
            self.finish()

    def update_image_progbar(self, i: int):
        self.image_prog_bar.setValue(i)
        if i == 100:
            self.finish()

    def finish(self):
        if self.finished == 2:
            logger.info("App starting")
            self.image_info.setText(self.tr("Starting..."))
            shared.args.offline = self.offline
            shared.init_api_response(self.api_results)
            self.start_app.emit()
        else:
            self.finished += 1

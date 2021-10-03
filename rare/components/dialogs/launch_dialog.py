import os
from logging import getLogger

from PyQt5.QtCore import Qt, pyqtSignal, QRunnable, QObject, QThreadPool
from PyQt5.QtWidgets import QDialog
from requests.exceptions import ConnectionError

from legendary.core import LegendaryCore
from legendary.models.game import GameAsset
from rare import image_dir
from rare.components.dialogs.login import LoginDialog
from rare.ui.components.dialogs.launch_dialog import Ui_LaunchDialog
from rare.utils.models import ApiResults
from rare.utils.utils import download_images

logger = getLogger("Login")


class ApiSignals(QObject):
    image_progress = pyqtSignal(int)
    result = pyqtSignal(object, str)


class ImageWorker(QRunnable):
    download_progress = pyqtSignal(int)

    def __init__(self, core: LegendaryCore):
        super(ImageWorker, self).__init__()
        self.core = core
        self.signal = ApiSignals()
        self.setAutoDelete(True)

    def run(self):
        download_images(self.signal.image_progress, self.core)
        self.signal.image_progress.emit(100)


class ApiRequestWorker(QRunnable):
    def __init__(self, text: str, function: callable, args: tuple):
        super(ApiRequestWorker, self).__init__()
        self.function, self.args = function, args
        self.signals = ApiSignals()
        self.text = text
        self.setAutoDelete(True)

    def run(self) -> None:
        result = self.function(*self.args)
        self.signals.result.emit(result, self.text)


class LaunchDialog(QDialog, Ui_LaunchDialog):
    quit_app = pyqtSignal(int)
    start_app = pyqtSignal(bool, ApiResults)
    finished = False

    def __init__(self, core: LegendaryCore, offline=False, parent=None):
        super(LaunchDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.core = core
        self.offline = offline
        self.thread_pool = QThreadPool()
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
            self.thread_pool.start(image_worker)

            api_requests = [
                ["gamelist", self.core.get_game_and_dlc_list, (True,)],
                ["32bit", self.core.get_game_and_dlc_list, (True, "Win32")],
                ["mac", self.core.get_game_and_dlc_list, (True, "Mac")],
                ["assets", self.core.egs.get_game_assets, ()],
                ["no_assets", self.core.get_non_asset_library_items, ()]
            ]
            for r in api_requests:
                worker = ApiRequestWorker(*r)
                worker.signals.result.connect(self.handle_api_worker_result)
                self.thread_pool.start(worker)

        else:
            self.finished = True
            self.api_results.game_list, self.api_results.dlcs = self.core.get_game_and_dlc_list(False)
            self.finish()

    def handle_api_worker_result(self, result, text):
        logger.debug("Api Request got from " + text)
        if text == "gamelist":
            self.api_results.game_list, self.api_results.dlcs = result
        elif text == "32bit":
            self.api_results.bit32_games = [i.app_name for i in result[0]]
        elif text == "mac":
            self.api_results.mac_games = [i.app_name for i in result[0]]
        elif text == "assets":
            assets = [GameAsset.from_egs_json(a) for a in result]
            self.core.lgd.assets = assets
            self.api_results.assets = assets
        elif text == "no_assets":
            self.api_results.no_asset_games = result[0]

        if self.api_results:
            self.finish()

    def update_image_progbar(self, i: int):
        self.image_prog_bar.setValue(i)
        if i == 100:
            self.finish()

    def finish(self):
        if self.finished:
            logger.info("App starting")
            self.image_info.setText(self.tr("Starting..."))
            self.start_app.emit(self.offline, self.api_results)
        else:
            self.finished = True

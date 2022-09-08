import platform
from logging import getLogger

from PyQt5.QtCore import Qt, pyqtSignal, QRunnable, QObject, QThreadPool, QSettings
from PyQt5.QtWidgets import QDialog, QApplication
from requests.exceptions import ConnectionError, HTTPError

from rare.components.dialogs.login import LoginDialog
from rare.models.apiresults import ApiResults
from rare.shared import LegendaryCoreSingleton, ArgumentsSingleton, ApiResultsSingleton, ImageManagerSingleton
from rare.ui.components.dialogs.launch_dialog import Ui_LaunchDialog
from rare.utils.misc import CloudWorker

logger = getLogger("LaunchDialog")


class LaunchWorker(QRunnable):
    class Signals(QObject):
        progress = pyqtSignal(int)
        result = pyqtSignal(object, str)
        finished = pyqtSignal()

    def __init__(self):
        super(LaunchWorker, self).__init__()
        self.setAutoDelete(True)
        self.signals = LaunchWorker.Signals()
        self.core = LegendaryCoreSingleton()

    def run(self):
        pass


class ImageWorker(LaunchWorker):
    def __init__(self):
        super(ImageWorker, self).__init__()
        self.image_manager = ImageManagerSingleton()

    def run(self):
        # Download Images
        games, dlcs = self.core.get_game_and_dlc_list(update_assets=True, skip_ue=False)
        self.signals.result.emit((games, dlcs), "gamelist")
        dlc_list = [dlc[0] for dlc in dlcs.values()]

        na_games, na_dlcs = self.core.get_non_asset_library_items(force_refresh=False, skip_ue=False)
        self.signals.result.emit(na_games, "no_assets")
        na_dlc_list = [dlc[0] for dlc in na_dlcs.values()]

        game_list = games + dlc_list + na_games + na_dlc_list

        for i, game in enumerate(game_list):
            if game.app_title == "Unreal Engine":
                game.app_title += f" {game.app_name.split('_')[-1]}"
                self.core.lgd.set_game_meta(game.app_name, game)
            self.image_manager.download_image_blocking(game)
            self.signals.progress.emit(int(i / len(game_list) * 100))
        self.signals.finished.emit()


class ApiRequestWorker(LaunchWorker):
    def __init__(self):
        super(ApiRequestWorker, self).__init__()
        self.settings = QSettings()

    def run(self) -> None:
        if self.settings.value("mac_meta", platform.system() == "Darwin", bool):
            try:
                result = self.core.get_game_and_dlc_list(update_assets=False, platform="Mac")
            except HTTPError:
                result = [], {}
        else:
            result = [], {}
        self.signals.result.emit(result, "mac")

        if self.settings.value("win32_meta", False, bool):
            try:
                result = self.core.get_game_and_dlc_list(update_assets=False, platform="Win32")
            except HTTPError:
                result = [], {}
        else:
            result = [], {}
        self.signals.result.emit(result, "32bit")


class LaunchDialog(QDialog):
    quit_app = pyqtSignal(int)
    start_app = pyqtSignal()
    completed = 0

    def __init__(self, parent=None):
        super(LaunchDialog, self).__init__(parent=parent)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(
            Qt.Window
            | Qt.Dialog
            | Qt.CustomizeWindowHint
            | Qt.WindowSystemMenuHint
            | Qt.WindowTitleHint
            | Qt.WindowMinimizeButtonHint
            | Qt.MSWindowsFixedSizeDialogHint
        )
        self.setWindowModality(Qt.WindowModal)
        self.ui = Ui_LaunchDialog()
        self.ui.setupUi(self)

        self.core = LegendaryCoreSingleton()
        self.args = ArgumentsSingleton()
        self.thread_pool = QThreadPool().globalInstance()
        self.api_results = ApiResults()

        self.login_dialog = LoginDialog(core=self.core, parent=self)

    def login(self):
        do_launch = True
        try:
            if self.args.offline:
                pass
            else:
                QApplication.instance().processEvents()
                # Force an update check and notice in case there are API changes
                self.core.check_for_updates(force=True)
                self.core.force_show_update = True
                if self.core.login():
                    logger.info("You are logged in")
                else:
                    raise ValueError("You are not logged in. Open Login Window")
        except ValueError as e:
            logger.info(str(e))
            # Do not set parent, because it won't show a task bar icon
            # Update: Inherit the same parent as LaunchDialog
            do_launch = self.login_dialog.login()
        except (HTTPError, ConnectionError) as e:
            logger.warning(e)
            self.args.offline = True
        finally:
            if do_launch:
                if not self.args.silent:
                    self.show()
                self.launch()
            else:
                self.quit_app.emit(0)

    def start_api_requests(self):
        # gamelist and no_asset games are from Image worker
        api_worker = ApiRequestWorker()
        api_worker.signals.result.connect(self.handle_api_worker_result)
        self.thread_pool.start(api_worker)

    def launch(self):

        if not self.args.offline:
            self.ui.image_info.setText(self.tr("Downloading Images"))
            image_worker = ImageWorker()
            image_worker.signals.result.connect(self.handle_api_worker_result)
            image_worker.signals.progress.connect(self.update_image_progbar)
            # lk: start the api requests worker after the manifests have been downloaded
            # lk: to avoid force updating the assets twice and causing inconsistencies
            image_worker.signals.finished.connect(self.start_api_requests)
            image_worker.signals.finished.connect(self.finish)
            self.thread_pool.start(image_worker)

            # cloud save from another worker, because it is used in cloud_save_utils too
            cloud_worker = CloudWorker()
            cloud_worker.signals.result_ready.connect(lambda x: self.handle_api_worker_result(x, "saves"))
            self.thread_pool.start(cloud_worker)

        else:
            self.completed = 2
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
        elif text == "no_assets":
            self.api_results.no_asset_games = result if result else []

        elif text == "32bit":
            self.api_results.bit32_games = [i.app_name for i in result[0]] if result else []
        elif text == "mac":
            self.api_results.mac_games = [i.app_name for i in result[0]] if result else []

        elif text == "saves":
            self.api_results.saves = result

        if self.api_results:
            self.finish()

    def update_image_progbar(self, i: int):
        self.ui.image_prog_bar.setValue(i)

    def finish(self):
        self.completed += 1
        if self.completed == 2:
            logger.info("App starting")
            self.ui.image_info.setText(self.tr("Starting..."))
            ApiResultsSingleton(self.api_results)
            self.completed += 1
            self.start_app.emit()

    def reject(self) -> None:
        if self.completed >= 3:
            super(LaunchDialog, self).reject()
        else:
            pass

import datetime
from dataclasses import dataclass
from logging import getLogger
from typing import Union, List

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool, Qt, QSettings
from PyQt5.QtWidgets import QDialog, QMessageBox, QSizePolicy, QLayout
from qtawesome import icon

from legendary.models.game import SaveGameStatus, InstalledGame, SaveGameFile
from rare import shared
from rare.ui.components.dialogs.sync_save_dialog import Ui_SyncSaveDialog

logger = getLogger("Cloud Saves")


@dataclass
class UploadModel:
    app_name: str
    date_time: datetime.datetime
    path: str


@dataclass
class DownloadModel:
    app_name: str
    latest_save: SaveGameFile
    path: str


class WorkerSignals(QObject):
    finished = pyqtSignal(str, str)


class SaveWorker(QRunnable):
    signals = WorkerSignals()

    def __init__(self, model: Union[UploadModel, DownloadModel]):
        super(SaveWorker, self).__init__()
        self.model = model

        self.setAutoDelete(True)

    def run(self) -> None:
        try:
            if isinstance(self.model, DownloadModel):
                shared.core.download_saves(self.model.app_name, self.model.latest_save.manifest_name, self.model.path)
            else:
                shared.core.upload_save(self.model.app_name, self.model.path, self.model.date_time)
        except Exception as e:
            self.signals.finished.emit(str(e), self.model.app_name)
            logger.error(str(e))
            return
        try:
            if isinstance(self.model, UploadModel):
                logger.info("Updating cloud saves...")
                result = shared.core.get_save_games(self.model.app_name)
                shared.api_results.saves = result
        except Exception as e:
            self.signals.finished.emit(str(e), self.model.app_name)
            logger.error(str(e))
            return

        self.signals.finished.emit("", self.model.app_name)


class CloudSaveDialog(QDialog, Ui_SyncSaveDialog):
    DOWNLOAD = 2
    UPLOAD = 1
    CANCEL = 0

    def __init__(self, igame: InstalledGame, dt_local: datetime.datetime, dt_remote: datetime.datetime, newer: str):
        super(CloudSaveDialog, self).__init__()
        self.setupUi(self)

        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)

        self.status = self.CANCEL

        self.title_label.setText(self.title_label.text() + igame.title)

        self.date_info_local.setText(dt_local.strftime("%A, %d. %B %Y %X"))
        self.date_info_remote.setText(dt_remote.strftime("%A, %d. %B %Y %X"))

        new_text = self.tr(" (newer)")
        if newer == "remote":
            self.cloud_gb.setTitle(self.cloud_gb.title() + new_text)
        elif newer == "local":
            self.local_gb.setTitle(self.local_gb.title() + new_text)

        self.icon_local.setPixmap(icon("mdi.harddisk").pixmap(128, 128))
        self.icon_remote.setPixmap(icon("mdi.cloud-outline").pixmap(128, 128))

        self.upload_button.clicked.connect(lambda: self.btn_clicked(self.UPLOAD))
        self.download_button.clicked.connect(lambda: self.btn_clicked(self.DOWNLOAD))
        self.cancel_button.clicked.connect(self.close)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.layout().setSizeConstraint(QLayout.SetFixedSize)

    def get_action(self):
        self.exec_()
        return self.status

    def btn_clicked(self, status):
        self.status = status
        self.close()


class CloudSaveUtils(QObject):
    sync_finished = pyqtSignal(str)

    def __init__(self):
        super(CloudSaveUtils, self).__init__()
        self.core = shared.core
        saves = shared.api_results.saves
        if not shared.args.offline:
            self.latest_saves = self.get_latest_saves(saves)
        else:
            self.latest_saves = dict()
        self.settings = QSettings()

        self.thread_pool = QThreadPool.globalInstance()

    def get_latest_saves(self, saves: List[SaveGameFile]) -> dict:
        save_games = set()
        for igame in self.core.get_installed_list():
            game = self.core.get_game(igame.app_name)
            if self.core.is_installed(igame.app_name) and game.supports_cloud_saves:
                save_games.add(igame.app_name)

        latest_saves = dict()
        for s in sorted(saves, key=lambda a: a.datetime):
            if s.app_name in save_games:
                latest_saves[s.app_name] = s
        return latest_saves

    def sync_before_launch_game(self, app_name, ignore_settings=False) -> int:
        if not ignore_settings:
            default = self.settings.value("auto_sync_cloud", True, bool)
            if not self.settings.value(f"{app_name}/auto_sync_cloud", default, bool):
                return False

        igame = self.core.get_installed_game(app_name)

        if not igame.save_path:
            try:
                savepath = self.core.get_save_path(app_name)
            except Exception as e:
                logger.error(e)
                savepath = ""
            if savepath:
                igame.save_path = savepath
                self.core.lgd.set_installed_game(app_name, igame)
                logger.info(f"Set save path of {igame.title} to {savepath}")
            elif not ignore_settings:  # sync on startup
                if QMessageBox.question(None, "Warning", self.tr(
                        "Could not compute cloud save path. Please set it in Game settings manually. \nDo you want to launch {} anyway?").format(
                    igame.title, QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes):
                    return False
                else:
                    raise ValueError("No savepath detected")
            else:
                QMessageBox.warning(None, "Warning",
                                    self.tr("No savepath found. Please set it in Game Settings manually"))
                return False

        res, (dt_local, dt_remote) = self.core.check_savegame_state(igame.save_path, self.latest_saves.get(app_name))

        if res == SaveGameStatus.NO_SAVE:
            return False

        if res != SaveGameStatus.SAME_AGE:
            newer = ""
            if res == SaveGameStatus.REMOTE_NEWER:
                newer = "remote"
            elif res == SaveGameStatus.LOCAL_NEWER:
                newer = "local"

            if res == SaveGameStatus.REMOTE_NEWER and not dt_local:
                self.download_saves(igame)
                return True

            elif res == SaveGameStatus.LOCAL_NEWER and not dt_remote:
                self.upload_saves(igame, dt_local)
                return True

            result = CloudSaveDialog(igame, dt_local, dt_remote, newer).get_action()
            if result == CloudSaveDialog.UPLOAD:
                self.upload_saves(igame, dt_local)
            elif result == CloudSaveDialog.DOWNLOAD:
                self.download_saves(igame)
            elif result == CloudSaveDialog.CANCEL:
                raise AssertionError()
            return True

        return False

    def game_finished(self, app_name, ignore_settings=False, always_ask: bool = False):
        if not ignore_settings:
            default = self.settings.value("auto_sync_cloud", True, bool)
            if not self.settings.value(f"{app_name}/auto_sync_cloud", default, bool):
                self.sync_finished.emit(app_name)
                return

        igame = self.core.get_installed_game(app_name)

        if not igame.save_path:
            try:
                savepath = self.core.get_save_path(app_name)
            except Exception as e:
                logger.error(e)
                savepath = ""
            if savepath:
                igame.save_path = savepath
                self.core.lgd.set_installed_game(app_name, igame)
                logger.info(f"Set save path of {igame.title} to {savepath}")
            else:
                QMessageBox.warning(None, "Warning", self.tr("No savepath set. Skip syncing with cloud"))
                return False

        res, (dt_local, dt_remote) = self.core.check_savegame_state(igame.save_path, self.latest_saves.get(app_name))

        if res == SaveGameStatus.LOCAL_NEWER and not always_ask:
            self.upload_saves(igame, dt_local)
            return

        elif res == SaveGameStatus.NO_SAVE and not always_ask:
            QMessageBox.warning(None, "No saves", self.tr(
                "There are no saves local and online. Maybe you have to change save path of {}").format(igame.title))
            self.sync_finished.emit(app_name)
            return

        elif res == SaveGameStatus.SAME_AGE and not always_ask:
            self.sync_finished.emit(app_name)
            return

        # Remote newer
        newer = ""
        if res == SaveGameStatus.REMOTE_NEWER:
            newer = "remote"
        elif res == SaveGameStatus.LOCAL_NEWER:
            newer = "local"
        result = CloudSaveDialog(igame, dt_local, dt_remote, newer).get_action()
        if result == CloudSaveDialog.UPLOAD:
            self.upload_saves(igame, dt_local)
        elif result == CloudSaveDialog.DOWNLOAD:
            self.download_saves(igame)

    def upload_saves(self, igame: InstalledGame, dt_local):
        logger.info("Uploading saves for " + igame.title)
        w = SaveWorker(UploadModel(igame.app_name, dt_local, igame.save_path))
        w.signals.finished.connect(self.worker_finished)
        self.thread_pool.start(w)

    def download_saves(self, igame):
        logger.info("Downloading saves for " + igame.title)
        w = SaveWorker(DownloadModel(igame.app_name, self.latest_saves.get(igame.app_name), igame.save_path))
        w.signals.finished.connect(self.worker_finished)
        self.thread_pool.start(w)

    def worker_finished(self, error_message: str, app_name: str):
        if not error_message:

            self.sync_finished.emit(app_name)
            self.latest_saves = self.get_latest_saves(shared.api_results.saves)
        else:
            QMessageBox.warning(None, "Warning", self.tr("Syncing with cloud failed: \n ") + error_message)
            self.sync_finished.emit(app_name)

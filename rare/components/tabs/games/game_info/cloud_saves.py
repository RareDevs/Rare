import os
from logging import getLogger

from PyQt5.QtCore import QThreadPool
from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox

from legendary.models.game import Game, InstalledGame, SaveGameStatus
from rare import shared
from rare.components.tabs.games.game_info.cloud_save_utils import DownloadWorker, UploadWorker, UploadModel, \
    DownloadModel
from rare.ui.components.tabs.games.game_info.cloud_saves import Ui_CloudSaves
from rare.utils.extra_widgets import PathEdit

logger = getLogger("Save Games")


class CloudSaves(QWidget, Ui_CloudSaves):
    latest_saves = dict()
    game: Game
    igame: InstalledGame

    # warn if true
    upload_anyway: bool = False
    download_anyway: bool = False

    def __init__(self, parent=None):
        super(CloudSaves, self).__init__(parent=parent)
        self.setupUi(self)
        self.core = shared.core

        self.save_path_edit = PathEdit(file_type=QFileDialog.Directory, ph_text=self.tr("Save path"))
        self.pathlayout.addWidget(self.save_path_edit)

        self.download_button.clicked.connect(self.download_save)
        self.upload_button.clicked.connect(self.upload_save)
        self.clean_saves_button.clicked.connect(self.cleanup_saves)

        saves = shared.api_results.saves
        # init latest saves
        save_games = set()
        for igame in self.core.get_installed_list():
            game = self.core.get_game(igame.app_name)
            if self.core.is_installed(igame.app_name) and game.supports_cloud_saves:
                save_games.add(igame.app_name)

        for s in sorted(saves, key=lambda a: a.datetime):
            if s.app_name in save_games:
                self.latest_saves[s.app_name] = s

        logger.info(f'Got {len(self.latest_saves)} remote save game(s)')

        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(1)

    def cleanup_saves(self):
        self.core.clean_saves(self.igame.app_name)
        logger.info("Cleanup saves for " + self.igame.title)
        self.update_game(self.game)

    def download_save(self):
        if self.download_anyway:
            reply = QMessageBox.question(self.parent().parent(), 'Confirm',
                                         self.tr(
                                             "Do you really want to download saves. It could overwrite your current saves"),
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
        logger.info("Downloading Saves for game " + self.igame.title)
        self.info_label.setText(self.tr("Downloading..."))
        self.upload_button.setDisabled(True)
        self.download_button.setDisabled(True)

        worker = DownloadWorker(
            DownloadModel(app_name=self.igame.app_name, latest_save=self.latest_saves[self.igame.app_name],
                          path=self.igame.save_path))
        worker.signals.error_message.connect(lambda msg: self.worker_finished(msg, "download"))
        self.thread_pool.start(worker)

    def upload_save(self):
        reply = QMessageBox.question(self.parent().parent(), 'Confirm',
                                     self.tr(
                                         "Do you really want to upload saves. It could overwrite your current saves"),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        logger.info("Uploading Saves for game " + self.igame.title)
        self.info_label.setText(self.tr("Uploading..."))
        self.upload_button.setDisabled(True)
        self.download_button.setDisabled(True)

        worker = UploadWorker(
            UploadModel(app_name=self.igame.app_name, date_time=self.dt_local, path=self.igame.save_path))
        worker.signals.error_message.connect(lambda msg: self.worker_finished(msg, "upload"))
        self.thread_pool.start(worker)

    def worker_finished(self, error_message: str, task):
        if not error_message:
            self.info_label.setText(self.tr("Upload finished") if task == "upload" else self.tr("Download finished"))
        else:
            text = self.tr("Upload failed") if task == "upload" else self.tr("Download failed")
            self.info_label.setText(text)
            QMessageBox.warning(self, "Warning", text + "\n" + error_message)
        self.update_game(self.game)

    def update_game(self, game: Game):
        self.game = game
        self.igame = self.core.get_installed_game(game.app_name)

        self.upload_button.setDisabled(False)
        self.upload_button.setToolTip("")
        self.upload_button.setText(self.tr("Upload"))

        self.download_button.setDisabled(False)
        self.download_button.setToolTip("")
        self.download_button.setText("Download")

        self.game_title.setText(f"<h2>{self.game.app_title}</h2>")
        self.info_label.setText("")

        self.upload_anyway = False
        self.download_anyway = False

        if not self.igame.save_path:
            try:
                save_path = self.core.get_save_path(self.igame.app_name)
            except Exception as e:
                logger.error(e)
                return
        else:
            save_path = self.igame.save_path

        if '%' in save_path or '{' in save_path:
            # status = self.tr("Path not found")
            logger.info("Could not find save path")
            self.igame.save_path = ""
        else:
            self.igame.save_path = save_path
            self.core.lgd.set_game_meta(self.igame.app_name, self.igame)

        if self.igame.save_path and not os.path.exists(self.igame.save_path):
            os.makedirs(self.igame.save_path)

        self.save_path_edit.setText(save_path)

        res, (self.dt_local, dt_remote) = self.core.check_savegame_state(self.igame.save_path,
                                                                         self.latest_saves.get(self.igame.app_name, ""))
        if self.dt_local:
            self.local_label.setText(self.dt_local.strftime("%A, %d. %B %Y %I:%M%p"))
        else:
            self.local_label.setText(self.tr("No local save"))

        if dt_remote:
            self.cloud_label.setText(str(dt_remote.strftime("%A, %d. %B %Y %I:%M%p")))
        else:
            self.cloud_label.setText(self.tr("No cloud save"))

        upload_anyway_text = self.tr("Upload anyway")
        dl_anyway_text = self.tr("Download anyway")

        if res == SaveGameStatus.NO_SAVE:
            self.download_button.setDisabled(True)
            self.upload_button.setDisabled(True)
            logger.debug('No cloud or local savegame found.')

        elif res == SaveGameStatus.SAME_AGE:
            logger.debug(f'Save game for "{self.igame.title}" is up to date')
            self.upload_button.setText(upload_anyway_text)
            self.upload_anyway = True
            self.download_button.setText(dl_anyway_text)
            self.download_anyway = True

        elif res == SaveGameStatus.REMOTE_NEWER:
            logger.debug(f'Cloud save for "{self.igame.title}" is newer')
            if self.dt_local:
                self.upload_button.setText(upload_anyway_text)
                self.upload_anyway = True
            else:
                self.upload_button.setDisabled(True)
                self.upload_button.setToolTip(self.tr("No local save"))

        elif res == SaveGameStatus.LOCAL_NEWER:
            if dt_remote:
                self.download_button.setText(dl_anyway_text)
                self.download_anyway = True
            else:
                self.download_button.setDisabled(True)
        else:
            QMessageBox.warning(self, "Warning", str(res))

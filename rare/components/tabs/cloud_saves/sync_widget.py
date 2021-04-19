import os
from logging import getLogger

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QGroupBox

from custom_legendary.core import LegendaryCore
from custom_legendary.models.game import InstalledGame, SaveGameStatus
from rare.components.dialogs.path_input_dialog import PathInputDialog

logger = getLogger("Sync")


def get_raw_save_path(app_name, core):
    game = core.lgd.get_game_meta(app_name)
    save_path = game.metadata['customAttributes'].get('CloudSaveFolder', {}).get('value')
    return save_path


class _UploadThread(QThread):
    signal = pyqtSignal()

    def __init__(self, app_name, date_time, save_path, core: LegendaryCore):
        super(_UploadThread, self).__init__()
        self.core = core
        self.app_name = app_name
        self.date_time = date_time
        self.save_path = save_path

    def run(self) -> None:
        try:
            self.core.upload_save(self.app_name, self.save_path, self.date_time)
        except Exception as e:
            logger.error(e)


class _DownloadThread(QThread):
    signal = pyqtSignal()

    def __init__(self, app_name, latest_save, save_path, core: LegendaryCore):
        super(_DownloadThread, self).__init__()
        self.core = core
        self.app_name = app_name
        self.latest_save = latest_save
        self.save_path = save_path

    def run(self) -> None:
        try:
            self.core.download_saves(self.app_name, self.latest_save.manifest_name, self.save_path, clean_dir=True)
        except Exception as e:
            logger.error(e)


class SyncWidget(QGroupBox):
    reload = pyqtSignal(str)

    def __init__(self, igame: InstalledGame, save, core: LegendaryCore):
        super(SyncWidget, self).__init__(igame.title)
        self.setObjectName("group")
        self.layout = QVBoxLayout()
        self.setContentsMargins(10, 20, 10, 20)
        self.thr = None
        self.core = core
        self.save = save
        self.logger = getLogger("Sync " + igame.app_name)
        self.game = self.core.get_game(igame.app_name)
        self.igame = igame
        self.has_save_path = True
        if not igame.save_path:
            try:
                save_path = self.core.get_save_path(igame.app_name)
            except Exception as e:
                self.logger.error(e)
                return
            if '%' in save_path or '{' in save_path:
                status = self.tr("Path not found")
                self.logger.info("Could not find save path")
            else:
                igame.save_path = save_path

        if not os.path.exists(igame.save_path):
            os.makedirs(igame.save_path)

        self.res, (self.dt_local, dt_remote) = self.core.check_savegame_state(igame.save_path, save)
        if self.res == SaveGameStatus.NO_SAVE:
            self.logger.info('No cloud or local savegame found.')
            return

        # game_title = QLabel(f"<h2>{igame.title}</h2>")

        if self.dt_local:
            local_save_date = QLabel(
                self.tr("Local Save date: ") + str(self.dt_local.strftime('%Y-%m-%d %H:%M:%S')))
        else:
            local_save_date = QLabel(self.tr("No Local Save files"))
        if dt_remote:
            cloud_save_date = QLabel(self.tr("Cloud save date: ") + str(dt_remote.strftime('%Y-%m-%d %H:%M:%S')))
        else:
            cloud_save_date = QLabel(self.tr("No Cloud saves"))

        if self.res == SaveGameStatus.SAME_AGE:
            self.logger.info(f'Save game for "{igame.title}" is up to date')
            status = self.tr("Game is up to date")
            self.upload_button = QPushButton(self.tr("Upload anyway"))
            self.download_button = QPushButton(self.tr("Download anyway"))
        elif self.res == SaveGameStatus.REMOTE_NEWER:
            status = self.tr("Cloud save is newer")
            self.download_button = QPushButton(self.tr("Download Cloud saves"))
            self.download_button.setStyleSheet("""
                           QPushButton{ background-color: lime}
                       """)
            self.upload_button = QPushButton(self.tr("Upload Saves"))
            self.logger.info(f'Cloud save for "{igame.title}" is newer:')
            self.logger.info(f'- Cloud save date: {dt_remote.strftime("%Y-%m-%d %H:%M:%S")}')
            if self.dt_local:
                self.logger.info(f'- Local save date: {self.dt_local.strftime("%Y-%m-%d %H:%M:%S")}')
            else:
                self.logger.info('- Local save date: N/A')
                self.upload_button.setDisabled(True)
                self.upload_button.setToolTip("No local save")

        elif self.res == SaveGameStatus.LOCAL_NEWER:
            status = self.tr("Local save is newer")
            self.upload_button = QPushButton(self.tr("Upload saves"))
            self.upload_button.setStyleSheet("""
                           QPushButton{ background-color: lime}
                       """)
            self.download_button = QPushButton(self.tr("Download saves"))
            self.logger.info(f'Local save for "{igame.title}" is newer')
            if dt_remote:
                self.logger.info(f'- Cloud save date: {dt_remote.strftime("%Y-%m-%d %H:%M:%S")}')
            else:
                self.logger.info('- Cloud save date: N/A')
                self.download_button.setDisabled(True)
            self.logger.info(f'- Local save date: {self.dt_local.strftime("%Y-%m-%d %H:%M:%S")}')
        else:
            self.logger.error(self.res)
            return

        self.upload_button.clicked.connect(self.upload)
        self.download_button.clicked.connect(self.download)
        self.info_text = QLabel(status)
        # self.layout.addWidget(game_title)
        self.layout.addWidget(local_save_date)
        self.layout.addWidget(cloud_save_date)

        save_path_layout = QHBoxLayout()

        self.raw_path = QLabel("Raw path: " + get_raw_save_path(self.game.app_name, self.core))
        self.raw_path.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.layout.addWidget(self.raw_path)

        self.save_path_text = QLabel(igame.save_path)
        self.save_path_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.save_path_text.setWordWrap(True)
        self.change_save_path = QPushButton(self.tr("Change path"))
        self.change_save_path.setFixedWidth(100)
        self.change_save_path.clicked.connect(self.change_path)
        save_path_layout.addWidget(self.save_path_text)
        save_path_layout.addWidget(self.change_save_path)
        self.layout.addLayout(save_path_layout)
        self.layout.addWidget(self.info_text)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.upload_button)
        button_layout.addWidget(self.download_button)
        self.layout.addLayout(button_layout)
        self.layout.addStretch(1)
        self.setLayout(self.layout)

    def change_path(self):
        path = PathInputDialog("Select directory", "Select savepath. Warning: Do not change if you are not sure",
                               self.igame.save_path).get_path()
        if path != "":
            self.igame.save_path = path
            self.core.lgd.set_installed_game(self.igame.app_name, self.igame)
            self.save_path_text.setText(self.igame.save_path)
            self.reload.emit(self.game.app_name)

    def upload(self):
        self.logger.info("Uploading Saves for game " + self.igame.title)
        self.info_text.setText(self.tr("Uploading..."))
        self.upload_button.setDisabled(True)
        self.download_button.setDisabled(True)
        self.thr = _UploadThread(self.igame.app_name, self.dt_local, self.igame.save_path, self.core)
        self.thr.finished.connect(self.uploaded)
        self.thr.start()

    def uploaded(self):
        self.info_text.setText(self.tr("Upload finished"))
        self.upload_button.setDisabled(False)
        self.reload.emit(self.game.app_name)

    def download(self):
        if not os.path.exists(self.igame.save_path):
            os.makedirs(self.igame.save_path)
        self.upload_button.setDisabled(True)
        self.download_button.setDisabled(True)
        self.logger.info("Downloading Saves for game " + self.igame.title)
        self.info_text.setText(self.tr("Downloading..."))
        self.thr = _DownloadThread(self.igame.app_name, self.save, self.igame.save_path, self.core)
        self.thr.finished.connect(self.downloaded)
        self.thr.start()

    def downloaded(self):
        self.info_text.setText(self.tr("Download finished"))
        self.upload_button.setDisabled(True)
        self.download_button.setDisabled(True)
        self.download_button.setStyleSheet("QPushButton{background-color: black}")
        self.reload.emit(self.game.app_name)

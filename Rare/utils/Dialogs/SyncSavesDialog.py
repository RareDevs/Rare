import os
from logging import getLogger

from PyQt5.QtCore import QThread, pyqtSignal, QObjectCleanupHandler
from PyQt5.QtWidgets import *
from legendary.core import LegendaryCore
from legendary.models.game import SaveGameStatus

from Rare.ext.QtExtensions import CustomQLabel, WaitingSpinner

logger = getLogger("Sync Saves")


class LoadThread(QThread):
    signal = pyqtSignal(list)

    def __init__(self, core: LegendaryCore):
        super(LoadThread, self).__init__()
        self.core = core

    def run(self) -> None:
        saves = self.core.get_save_games()
        self.signal.emit(saves)


class SyncGame(QWidget):
    def __init__(self):
        super(SyncGame, self).__init__()


class SyncSavesDialog(QDialog):
    def __init__(self, core: LegendaryCore):
        super(SyncSavesDialog, self).__init__()
        self.core = core
        layout = QVBoxLayout()
        layout.addWidget(WaitingSpinner())
        layout.addWidget(QLabel("<h4>Loading Cloud Saves</h4>"))
        self.setLayout(layout)

        self.start_thread = LoadThread(self.core)
        self.start_thread.signal.connect(self.setup_ui)
        self.start_thread.start()
        self.igames = self.core.get_installed_list()
        # self.igames = self.core.get_installed_list()
        # self.saves = self.core.get_save_games()
        # latest_save = dict()

        # for save in sorted(self.saves, key=lambda a: a.datetime):
        #    latest_save[save.app_name] = save

        # self.setup_ui()

    def setup_ui(self, saves: list):
        self.start_thread.disconnect()
        QObjectCleanupHandler().add(self.layout())
        self.main_layout = QVBoxLayout()
        self.title = CustomQLabel("<h1>Cloud Saves</h1>\nFound Saves for folowing Games")
        self.sync_all_button = QPushButton("Sync all games")
        self.main_layout.addWidget(self.title)
        self.main_layout.addWidget(self.sync_all_button)
        self.status = {}

        latest_save = {}
        for i in saves:
            latest_save[i.app_name] = i
        logger.info(f'Got {len(latest_save)} remote save game(s)')

        if len(latest_save) == 0:
            QMessageBox.information("No Games Found", "Your games don't support cloud save")
            self.close()
            return
        for igame in self.igames:
            game = self.core.get_game(igame.app_name)
            if not game.supports_cloud_saves:
                continue
            logger.info(f'Checking "{igame.title}" ({igame.app_name})')

            if not igame.save_path:
                save_path = self.core.get_save_path(igame.app_name)
                if '%' in save_path or '{' in save_path:
                    status = "PathNotFound"
                    logger.info("Could not find save_path")
                else:
                    igame.save_path = save_path

            if not os.path.exists(igame.save_path):
                os.makedirs(igame.save_path)

            res, (dt_local, dt_remote) = self.core.check_savegame_state(igame.save_path,
                                                                        latest_save.get(igame.app_name))
            if res == SaveGameStatus.NO_SAVE:
                logger.info('No cloud or local savegame found.')
                continue
            widget = QWidget()
            layout = QVBoxLayout()
            game_title = CustomQLabel(f"<h2>{igame.title}</h2>")
            local_save_date = CustomQLabel(f"Local Save date: {dt_local.strftime('%Y-%m-%d %H:%M:%S')}")
            cloud_save_date = CustomQLabel(f"Cloud save date: {dt_remote.strftime('%Y-%m-%d %H:%M:%S')}")

            if res == SaveGameStatus.SAME_AGE:
                logger.info(f'Save game for "{igame.title}" is up to date')
                status = "Game is up to date"
                upload_button = QPushButton("Upload anyway")
                download_button = QPushButton("Download anyway")
            if res == SaveGameStatus.REMOTE_NEWER:
                status = "Cloud save is newer"
                download_button = QPushButton("Download Cloud saves")
                download_button.setStyleSheet("""
                    QPushButton{ background-color: lime}
                """)
                upload_button = QPushButton("Upload Saves")
                logger.info(f'Cloud save for "{igame.title}" is newer:')
                logger.info(f'- Cloud save date: {dt_remote.strftime("%Y-%m-%d %H:%M:%S")}')
                if dt_local:
                    logger.info(f'- Local save date: {dt_local.strftime("%Y-%m-%d %H:%M:%S")}')
                else:
                    logger.info('- Local save date: N/A')
                    upload_button.setDisabled(True)
                    upload_button.setToolTip("No local save")

            elif res == SaveGameStatus.LOCAL_NEWER:
                status = "local is newer"
                upload_button = QPushButton("Upload saves")
                upload_button.setStyleSheet("""
                    QPushButton{ background-color: lime}
                """)
                download_button = QPushButton("Download saves")
                logger.info(f'Local save for "{igame.title}" is newer')
                if dt_remote:
                    logger.info(f'- Cloud save date: {dt_remote.strftime("%Y-%m-%d %H:%M:%S")}')
                else:
                    logger.info('- Cloud save date: N/A')
                    download_button.setDisabled(True)
                logger.info(f'- Local save date: {dt_local.strftime("%Y-%m-%d %H:%M:%S")}')
            upload_button.app_name = igame.app_name
            download_button.app_name = igame.app_name
            upload_button.clicked.connect(lambda: self.upload(upload_button.app_name))
            download_button.clicked.connect(lambda: self.download_save(download_button.app_name))
            mini_layout = QHBoxLayout()
            mini_layout.addWidget(upload_button)
            mini_layout.addWidget(download_button)
            layout.addWidget(game_title)
            layout.addWidget(local_save_date)
            layout.addWidget(cloud_save_date)
            layout.addWidget(CustomQLabel(status))
            layout.addLayout(mini_layout)
            self.main_layout.addLayout(layout)
            self.status[igame.app_name] = res, dt_remote, dt_local, igame.save_path, latest_save[igame.app_name]

        self.setLayout(self.main_layout)

    def download_save(self, app_name):
        logger.info('Downloading saves ')
        res, dt_remote, dt_local, save_path, latest_save = self.status[app_name]
        self.core.download_saves(app_name, latest_save.manifest_name, save_path)
        # todo Threading

    def upload(self, app_name):
        logger.info("Uplouding saves")
        res, dt_remote, dt_local, save_path, latest_save = self.status[app_name]
        self.core.upload_save(app_name, save_path, dt_local)

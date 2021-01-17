from logging import getLogger

from PyQt5.QtCore import QThread, pyqtSignal, QObjectCleanupHandler
from PyQt5.QtWidgets import *
from legendary.core import LegendaryCore
from legendary.models.game import SaveGameStatus

from Rare.ext.QtExtensions import CustomQLabel, WaitingSpinner
from Rare.utils.Dialogs.PathInputDialog import PathInputDialog
from Rare.utils.Dialogs.SyncSaves.SyncWidget import SyncWidget

logger = getLogger("Sync Saves")


class UploadThread(QThread):
    signal = pyqtSignal(str)

    def __init__(self, args):
        super(UploadThread, self).__init__()
        self.args = args

    def run(self):
        logger.info("Uplouding saves")
        res, dt_remote, dt_local, save_path, latest_save = self.status[app_name]
        self.core.upload_save(app_name, save_path, dt_local)


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


# noinspection PyAttributeOutsideInit
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

    def setup_ui(self, saves: list):
        self.start_thread.disconnect()
        QObjectCleanupHandler().add(self.layout())
        self.main_layout = QVBoxLayout()
        self.title = CustomQLabel(
            f"<h1>" + self.tr("Cloud Saves") + "</h1>\n" + self.tr("Found Saves for folowing Games"))
        self.sync_all_button = QPushButton(self.tr("Sync all games"))
        self.sync_all_button.clicked.connect(self.sync_all)
        self.main_layout.addWidget(self.title)
        self.main_layout.addWidget(self.sync_all_button)

        latest_save = {}
        for i in saves:
            latest_save[i.app_name] = i
        logger.info(f'Got {len(latest_save)} remote save game(s)')
        if len(latest_save) == 0:
            QMessageBox.information(self.tr("No Games Found"), self.tr("Your games don't support cloud save"))
            self.close()
            return
        self.widgets = []

        for igame in self.igames:
            game = self.core.get_game(igame.app_name)
            if not game.supports_cloud_saves:
                continue
            if latest_save.get(igame.app_name):
                sync_widget = SyncWidget(igame, latest_save[igame.app_name], self.core)
            else:
                continue
            self.main_layout.addWidget(sync_widget)
            self.widgets.append(sync_widget)

        self.ok_button = QPushButton("Ok")
        self.ok_button.clicked.connect(lambda: self.close())
        self.main_layout.addWidget(self.ok_button)

        self.setLayout(self.main_layout)

    def sync_all(self):
        for w in self.widgets:
            if not w.igame.save_path:
                save_path = self.core.get_save_path(w.igame.app_name)
                if '%' in save_path or '{' in save_path:
                    self.logger.info("Could not find save_path")
                    save_path = PathInputDialog(self.tr("Found no savepath"),
                                                self.tr("No save path was found. Please select path or skip"))
                    if save_path == "":
                        continue
                else:
                    w.igame.save_path = save_path
            if w.res == SaveGameStatus.SAME_AGE:
                continue
            if w.res == SaveGameStatus.REMOTE_NEWER:
                w.download()
            elif w.res == SaveGameStatus.LOCAL_NEWER:
                w.upload()

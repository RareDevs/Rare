from logging import getLogger

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import *
from custom_legendary.core import LegendaryCore
from custom_legendary.models.game import SaveGameStatus

from Rare.Components.Dialogs.PathInputDialog import PathInputDialog
from Rare.Components.Tabs.CloudSaves.SyncWidget import SyncWidget
from Rare.utils.QtExtensions import WaitingSpinner

logger = getLogger("Sync Saves")


class LoadThread(QThread):
    signal = pyqtSignal(list)

    def __init__(self, core: LegendaryCore):
        super(LoadThread, self).__init__()
        self.core = core

    def run(self) -> None:
        saves = self.core.get_save_games()
        self.signal.emit(saves)


class SyncSaves(QScrollArea):

    def __init__(self, core: LegendaryCore):
        super(SyncSaves, self).__init__()
        self.core = core
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(WaitingSpinner())
        layout.addWidget(QLabel("<h4>Loading Cloud Saves</h4>"))
        layout.addStretch()
        self.widget.setLayout(layout)
        self.setWidget(self.widget)

        self.start_thread = LoadThread(self.core)
        self.start_thread.signal.connect(self.setup_ui)
        self.start_thread.start()
        self.igames = self.core.get_installed_list()

    def setup_ui(self, saves: list):
        self.start_thread.disconnect()

        self.main_layout = QVBoxLayout()
        self.title = QLabel(
            f"<h1>" + self.tr("Cloud Saves") + "</h1>\n" + self.tr("Found Saves for folowing Games"))
        self.sync_all_button = QPushButton(self.tr("Sync all games"))
        self.sync_all_button.clicked.connect(self.sync_all)
        self.main_layout.addWidget(self.title)
        self.main_layout.addWidget(self.sync_all_button)

        latest_save = {}
        for i in sorted(saves, key=lambda a: a.datetime):
            latest_save[i.app_name] = i

        logger.info(f'Got {len(latest_save)} remote save game(s)')
        if len(latest_save) == 0:
            # QMessageBox.information(self.tr("No Games Found"), self.tr("Your games don't support cloud save"))
            self.widget = QLabel("No Games found, supporting cloud saves")
            self.setWidget(self.widget)
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

        self.widget = QWidget()
        self.widget.setLayout(self.main_layout)
        self.setWidget(self.widget)

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

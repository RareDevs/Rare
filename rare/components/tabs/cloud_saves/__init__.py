from logging import getLogger

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import *

from custom_legendary.core import LegendaryCore
from custom_legendary.models.game import SaveGameStatus
from rare.components.dialogs.path_input_dialog import PathInputDialog
from rare.components.tabs.cloud_saves.sync_widget import SyncWidget
from rare.utils.extra_widgets import WaitingSpinner

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
    finished = pyqtSignal(str)

    def __init__(self, core: LegendaryCore, parent):
        super(SyncSaves, self).__init__(parent=parent)
        self.core = core
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.load_saves()

    def load_saves(self, app_name=None, auto=False):
        self.widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(WaitingSpinner())
        layout.addWidget(QLabel("<h4>Loading Cloud Saves</h4>"))
        layout.addStretch()
        self.widget.setLayout(layout)
        self.setWidget(self.widget)

        self.start_thread = LoadThread(self.core)
        self.start_thread.signal.connect(lambda x: self.setup_ui(x, app_name, auto))
        self.start_thread.start()
        self.igames = self.core.get_installed_list()

    def setup_ui(self, saves: list, app_name, auto=False):
        self.start_thread.disconnect()
        self.main_layout = QVBoxLayout()
        self.title = QLabel(
            f"<h1>" + self.tr("Cloud Saves") + "</h1>\n" + self.tr("Found Saves for folowing Games"))
        self.main_layout.addWidget(self.title)

        saves_games = []
        for i in saves:
            if not i.app_name in saves_games and self.core.is_installed(i.app_name):
                saves_games.append(i.app_name)
        if len(saves_games) == 0:
            # QMessageBox.information(self.tr("No Games Found"), self.tr("Your games don't support cloud save"))
            self.title.setText(
                f"<h1>" + self.tr("Cloud Saves") + "</h1>\n" + self.tr("Your games does not support Cloud Saves"))
            self.setWidget(self.title)
            return

        self.sync_all_button = QPushButton(self.tr("Sync all games"))
        self.sync_all_button.clicked.connect(self.sync_all)
        self.main_layout.addWidget(self.sync_all_button)

        latest_save = {}
        for i in sorted(saves, key=lambda a: a.datetime):
            latest_save[i.app_name] = i

        logger.info(f'Got {len(latest_save)} remote save game(s)')

        self.widgets = []
        for igame in self.igames:
            game = self.core.get_game(igame.app_name)
            if not game.supports_cloud_saves:
                continue
            if latest_save.get(igame.app_name):
                sync_widget = SyncWidget(igame, latest_save[igame.app_name], self.core)
            else:
                continue
            sync_widget.reload.connect(self.reload)
            self.main_layout.addWidget(sync_widget)
            self.widgets.append(sync_widget)

        self.widget = QWidget()
        self.main_layout.addStretch(1)
        self.widget.setLayout(self.main_layout)
        self.setWidgetResizable(True)
        self.setWidget(self.widget)

        if auto:
            self.save(app_name, True)

    def reload(self, app_name, auto=False):
        self.finished.emit(app_name)
        self.setWidget(QWidget())
        self.load_saves(auto)

    def sync_game(self, app_name, from_game_finish_auto=True):
        self.setWidget(QWidget())
        self.load_saves(app_name, from_game_finish_auto)

    def save(self, app_name, from_game_finish_auto=True):
        for w in self.widgets:
            if w.igame.app_name == app_name:
                widget = w
                break
        else:
            logger.warning("An Error occurred. Game does not support cloud saves")
            return

        if widget.res == SaveGameStatus.SAME_AGE:
            logger.info("Game is up to date")
        elif widget.res == SaveGameStatus.LOCAL_NEWER:
            widget.upload()
        elif widget.res == SaveGameStatus.REMOTE_NEWER:
            if from_game_finish_auto:
                if QMessageBox.question(self, "Really", self.tr("You finished playing game, but Remote game is newer. "
                                                                "Do you want to download anyway? This could remove "
                                                                "your game progress. Please check your save path or "
                                                                "make a backup"),
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
                    widget.download()
                else:
                    logger.info("Cancel Download")
        self.finished.emit(app_name)

    def sync_all(self):
        logger.info("Sync all Games")
        for w in self.widgets:
            if not w.igame.save_path:
                save_path = self.core.get_save_path(w.igame.app_name)
                if '%' in save_path or '{' in save_path:
                    self.logger.info_label("Could not find save_path")
                    save_path = PathInputDialog(self.tr("Found no savepath"),
                                                self.tr("No save path was found. Please select path or skip"))
                    if save_path == "":
                        continue
                else:
                    w.igame.save_path = save_path
            if w.res == SaveGameStatus.SAME_AGE:
                continue
            if w.res == SaveGameStatus.REMOTE_NEWER:
                logger.info("Download")
                w.download()
            elif w.res == SaveGameStatus.LOCAL_NEWER:
                logger.info("Upload")
                w.upload()

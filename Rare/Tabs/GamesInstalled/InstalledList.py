import json
import os
import string
from logging import getLogger

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from legendary.core import LegendaryCore

from Rare.Tabs.GamesInstalled.GameWidget import GameWidget
from Rare.utils import legendaryUtils
from Rare.utils.Dialogs.SyncSaves.SyncSavesDialog import SyncSavesDialog

logger = getLogger("InstalledList")


class GameListInstalled(QScrollArea):
    def __init__(self, core: LegendaryCore):
        super(GameListInstalled, self).__init__()

        self.core = core
        self.init_ui()

        # self.setLayout(self.layout)

    def init_ui(self):
        self.widget = QWidget()
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.layout = QVBoxLayout()
        mini_layout = QHBoxLayout()
        self.update_button = QPushButton("Manually reload Games")
        self.update_button.clicked.connect(self.update_list)
        mini_layout.addWidget(self.update_button)
        self.upload_button = QPushButton("Cloud Saves")
        mini_layout.addWidget(self.upload_button)
        self.upload_button.clicked.connect(self.sync_saves)
        self.layout.addLayout(mini_layout)
        self.widgets = {}
        games = sorted(self.core.get_installed_list(), key=lambda game: game.title)
        if games:
            for i in games:
                widget = GameWidget(i, self.core)
                widget.signal.connect(self.remove_game)
                self.widgets[i.app_name] = widget
                self.layout.addWidget(widget)

        else:
            not_installed_label = QLabel("No Games are installed. Do you want to import them?")
            not_installed_button = QPushButton("Import Games")
            not_installed_button.clicked.connect(self.import_games_prepare)
            self.layout.addWidget(not_installed_label)
            self.layout.addWidget(not_installed_button)

        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)

    def remove_game(self, app_name: str):
        logger.info(f"Uninstall {app_name}")
        legendaryUtils.uninstall(app_name=app_name, core=self.core)
        self.widgets[app_name].setVisible(False)
        self.layout.removeWidget(self.widgets[app_name])
        self.widgets[app_name].deleteLater()
        self.widgets.pop(app_name)

    def import_games_prepare(self):
        # Automatically import from windows
        imported = 0
        if os.name == "nt":
            available_drives = ['%s:' % d for d in string.ascii_uppercase if os.path.exists('%s:' % d)]
            for drive in available_drives:
                path = f"{drive}/Program Files/Epic Games/"
                if os.path.exists(path):
                    imported += self.auto_import_games(path)

        else:
            possible_wineprefixes = [os.path.expanduser("~/.wine/"), os.path.expanduser("~/Games/epic-games-store/")]
            for wine_prefix in possible_wineprefixes:
                imported += self.auto_import_games(f"{wine_prefix}drive_c/Program Files/Epic Games/")
        if imported > 0:
            QMessageBox.information(self, "Imported Games", f"Successfully imported  {imported} Games")
            logger.info("Restarting app to import games")
        else:
            QMessageBox.information(self, "Imported Games", "No Games were found")

    def auto_import_games(self, game_path):
        imported = 0
        if not os.path.exists(game_path):
            return 0
        if os.listdir(game_path) == 0:
            logger.info(f"No Games found in {game_path}")
            return 0
        for path in os.listdir(game_path):
            json_path = game_path + path + "/.egstore"
            print(json_path)
            if not os.path.isdir(json_path):
                logger.info(f"Game at {game_path + path} doesn't exist")
                continue

            for file in os.listdir(json_path):
                if file.endswith(".mancpn"):
                    app_name = json.load(open(os.path.join(json_path, file)))["AppName"]
                    if legendaryUtils.import_game(self.core, app_name, game_path + path):
                        imported += 1
        return imported

    def update_list(self):
        self.core = LegendaryCore()
        del self.widget
        self.setWidget(QWidget())
        self.init_ui()
        self.update()

    def sync_saves(self):
        SyncSavesDialog(self.core).exec_()

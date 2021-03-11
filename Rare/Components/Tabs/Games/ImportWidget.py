import json
import os
import string
from logging import getLogger

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QVBoxLayout, QFileDialog, QMessageBox
from qtawesome import icon

from Rare.utils import LegendaryApi
from Rare.utils.QtExtensions import PathEdit

logger = getLogger("Import")


class ImportWidget(QWidget):
    update_list = pyqtSignal()

    def __init__(self, core):
        super(ImportWidget, self).__init__()
        self.core = core
        self.main_layout = QHBoxLayout()
        self.back_button = QPushButton(icon("mdi.keyboard-backspace", color="white"), self.tr("Back"))
        self.right_layout = QVBoxLayout()
        self.right_layout.addWidget(self.back_button)
        self.right_layout.addStretch(1)
        self.main_layout.addLayout(self.right_layout)
        self.back_button.setFixedWidth(75)
        self.layout = QVBoxLayout()

        self.title = QLabel("<h2>Import Game</h2")
        self.layout.addWidget(self.title)

        self.import_one_game = QLabel(f"<h3>{self.tr('Import existing game')}</h3>")
        self.layout.addWidget(self.import_one_game)

        self.import_game_info = QLabel(self.tr("Select path to game"))
        self.layout.addWidget(self.import_game_info)

        self.path_edit = PathEdit(os.path.expanduser("~"), QFileDialog.DirectoryOnly)
        self.layout.addWidget(self.path_edit)

        self.import_button = QPushButton(self.tr("Import Game"))
        self.layout.addWidget(self.import_button)
        self.import_button.clicked.connect(self.import_game)

        self.layout.addStretch(1)

        self.auto_import = QLabel(f"<h3>{self.tr('Auto import all existing games')}</h3>")
        self.layout.addWidget(self.auto_import)
        self.auto_import_button = QPushButton(self.tr("Import all games from Epic Games Launcher"))
        self.auto_import_button.clicked.connect(self.import_games_prepare)
        self.layout.addWidget(self.auto_import_button)
        self.layout.addStretch(1)

        self.main_layout.addLayout(self.layout)
        # self.main_layout.addStretch(1)
        self.setLayout(self.main_layout)

    def import_game(self, path=None):
        if not path:
            path = self.path_edit.text()
        if not path.endswith("/"):
            path = path + "/"

        for i in os.listdir(os.path.join(path, ".egstore")):
            if i.endswith(".mancpn"):
                file = path + ".egstore/" + i
                break
        else:
            logger.warning("File was not found")
            return
        app_name = json.load(open(file, "r"))["AppName"]
        if LegendaryApi.import_game(self.core, app_name=app_name, path=path):
            self.update_list.emit()
        else:
            logger.warning("Failed to import" + app_name)
            return

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
                    if LegendaryApi.import_game(self.core, app_name, game_path + path):
                        imported += 1
        return imported

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
            QMessageBox.information(self, "Imported Games", self.tr("Successfully imported {} Games").format(imported))
            self.update_list.emit()
            logger.info("Restarting app to import games")
        else:
            QMessageBox.information(self, "Imported Games", "No Games were found")

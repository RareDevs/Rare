import json
import os
from logging import getLogger

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QVBoxLayout, QFileDialog, QLineEdit, \
    QGroupBox
from qtawesome import icon

from custom_legendary.core import LegendaryCore
from rare.utils import legendary_utils
from rare.utils.extra_widgets import PathEdit

logger = getLogger("Import")


class ImportWidget(QWidget):
    update_list = pyqtSignal(str)

    def __init__(self, core: LegendaryCore, parent):
        super(ImportWidget, self).__init__(parent=parent)
        self.core = core
        self.game_list = [i.app_name for i in self.core.get_game_list()]

        self.main_layout = QHBoxLayout()
        self.back_button = QPushButton(icon("mdi.keyboard-backspace"), self.tr("Back"))
        self.right_layout = QVBoxLayout()
        self.right_layout.addWidget(self.back_button)
        self.right_layout.addStretch(1)
        self.main_layout.addLayout(self.right_layout)
        self.back_button.setFixedWidth(75)
        self.layout = QVBoxLayout()

        self.title = QLabel("<h2>Import Game</h2")
        self.layout.addWidget(self.title)

        # self.import_one_game = QLabel(f"<h3>{self.tr('Import existing game from Epic Games Launcher')}</h3>")
        self.import_one_game = QGroupBox(self.tr('Import existing game from Epic Games Launcher'))
        self.import_one_game.setObjectName("group")
        self.gb_layout = QVBoxLayout()

        self.import_game_info = QLabel(self.tr("Select path to game"))
        self.gb_layout.addWidget(self.import_game_info)

        self.override_app_name_label = QLabel(
            self.tr("Override app name (Only if the app could not find the app name)"))
        self.override_app_name_label.setWordWrap(True)
        self.app_name_input = QLineEdit()
        self.app_name_input.setFixedHeight(32)
        minilayout = QHBoxLayout()
        minilayout.addStretch(1)
        self.indicator_label = QLabel("")
        minilayout.addWidget(self.indicator_label)
        self.app_name_input.setLayout(minilayout)
        self.app_name_input.textChanged.connect(self.app_name_changed)

        self.path_edit = PathEdit(os.path.expanduser("~"), QFileDialog.DirectoryOnly, edit_func=self.path_changed)
        self.gb_layout.addWidget(self.path_edit)

        self.gb_layout.addWidget(self.override_app_name_label)
        self.gb_layout.addWidget(self.app_name_input)

        self.info_label = QLabel("")
        self.gb_layout.addWidget(self.info_label)
        self.import_button = QPushButton(self.tr("Import Game"))
        self.gb_layout.addWidget(self.import_button)
        self.import_button.clicked.connect(self.import_game)

        self.import_one_game.setLayout(self.gb_layout)

        self.layout.addWidget(self.import_one_game)

        self.auto_import = QLabel(
            f"<h4>{self.tr('To import games from Epic Games Store, please enable EGL Sync in legendary settings')}</h4>")
        self.layout.addWidget(self.auto_import)
        self.layout.addStretch(1)

        self.main_layout.addLayout(self.layout)
        # self.main_layout.addStretch(1)
        self.setLayout(self.main_layout)

    def app_name_changed(self, text):
        if text in self.game_list:
            self.indicator_label.setPixmap(icon("ei.ok-sign", color="green").pixmap(16, 16))
        else:
            self.indicator_label.setPixmap(icon("ei.remove-sign", color="red").pixmap(16, 16))

    def path_changed(self, path):
        if os.path.exists(path):
            if os.path.exists(os.path.join(path, ".egstore")):
                self.app_name_input.setText(self.find_app_name(path))

    def find_app_name(self, path):
        if not os.path.exists(os.path.join(path, ".egstore")):
            return None
        for i in os.listdir(os.path.join(path, ".egstore")):
            if i.endswith(".mancpn"):
                file = os.path.join(path, ".egstore", i)
                break
        else:
            logger.warning("File was not found")
            return None
        return json.load(open(file, "r"))["AppName"]

    def import_game(self, path=None):
        app_name = self.app_name_input.text()
        if not path:
            path = self.path_edit.text()
        if not app_name:
            # try to find app name
            if a_n := self.find_app_name(path):
                app_name = a_n
            else:
                self.info_label.setText(self.tr("Could not find app name"))
                return

        if legendary_utils.import_game(self.core, app_name=app_name, path=path):
            self.info_label.setText(self.tr("Successfully imported {}. Reload library").format(
                self.core.get_installed_game(app_name).title))
            self.app_name_input.setText("")

            self.update_list.emit(app_name)
        else:
            logger.warning("Failed to import" + app_name)
            self.info_label.setText(self.tr("Failed to import {}").format(app_name))
            return

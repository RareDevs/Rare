import json
import os
from logging import getLogger
from typing import Tuple

from PyQt5.QtWidgets import QFileDialog, QGroupBox

import rare.shared as shared
from rare.ui.components.tabs.games.import_sync.import_group import Ui_ImportGroup
from rare.utils import legendary_utils
from rare.utils.extra_widgets import IndicatorLineEdit, PathEdit

logger = getLogger("Import")


class ImportGroup(QGroupBox, Ui_ImportGroup):
    def __init__(self, parent=None):
        super(ImportGroup, self).__init__(parent=parent)
        self.setupUi(self)
        self.core = shared.core
        self.game_list = [i.app_name for i in self.core.get_game_list()]

        self.path_edit = PathEdit(
            self.core.get_default_install_dir(),
            QFileDialog.DirectoryOnly,
            edit_func=self.path_edit_cb,
            parent=self
        )
        self.path_edit.textChanged.connect(self.path_changed)
        self.path_edit_layout.addWidget(self.path_edit)

        self.app_name = IndicatorLineEdit(
            ph_text=self.tr("Use in case the app name was not found automatically"),
            edit_func=self.app_name_edit_cb,
            parent=self
        )
        self.app_name.textChanged.connect(self.app_name_changed)
        self.app_name_layout.addWidget(self.app_name)

        self.import_button.setEnabled(False)
        self.import_button.clicked.connect(self.import_game)

    def path_edit_cb(self, path) -> Tuple[bool, str]:
        if os.path.exists(path):
            if os.path.exists(os.path.join(path, ".egstore")):
                return True, path
        return False, path

    def path_changed(self, path):
        if self.path_edit.is_valid:
            self.app_name.setText(self.find_app_name(path))
        else:
            self.app_name.setText(str())

    def app_name_edit_cb(self, text) -> Tuple[bool, str]:
        if not text:
            return False, text
        if text in self.game_list:
            return True, text
        else:
            return False, text

    def app_name_changed(self, text):
        if self.app_name.is_valid:
            self.import_button.setEnabled(True)
        else:
            self.import_button.setEnabled(False)

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
        app_name = self.app_name.text()
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
            self.app_name.setText("")

            shared.signals.update_gamelist.emit(app_name)
        else:
            logger.warning("Failed to import" + app_name)
            self.info_label.setText(self.tr("Failed to import {}").format(app_name))
            return

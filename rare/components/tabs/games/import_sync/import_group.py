import json
import os
from logging import getLogger
from typing import List, Tuple

from PyQt5.QtCore import Qt, QModelIndex, pyqtSignal
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QFileDialog, QGroupBox, QCompleter, QTreeView, QHeaderView

import rare.shared as shared
from rare.ui.components.tabs.games.import_sync.import_group import Ui_ImportGroup
from rare.utils import legendary_utils
from rare.utils.extra_widgets import IndicatorLineEdit, PathEdit

logger = getLogger("Import")


class AppNameCompleter(QCompleter):
    activated = pyqtSignal(str)

    def __init__(self, app_names: List, parent=None):
        super(AppNameCompleter, self).__init__(parent)
        # pylint: disable=E1136
        super(AppNameCompleter, self).activated[QModelIndex].connect(self.__activated_idx)

        model = QStandardItemModel(len(app_names), 2)
        for idx, game in enumerate(app_names):
            app_name, app_title = game
            model.setData(model.index(idx, 0), app_title)
            model.setData(model.index(idx, 1), app_name)
        self.setModel(model)

        treeview = QTreeView()
        self.setPopup(treeview)
        treeview.setRootIsDecorated(False)
        treeview.header().hide()
        treeview.header().setSectionResizeMode(0, QHeaderView.Stretch)
        treeview.header().setSectionResizeMode(1, QHeaderView.Stretch)

        # listview = QListView()
        # self.setPopup(listview)
        # # listview.setModelColumn(1)

        self.setFilterMode(Qt.MatchContains)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        # self.setCompletionMode(QCompleter.UnfilteredPopupCompletion)

    def __activated_idx(self, idx):
        # lk: don't even look at this in a funny way, it will die of shame
        # lk: Note to self, the completer and popup models are different.
        # lk: Getting the index from the popup and trying to use it in the completer will return invalid results
        if isinstance(idx, QModelIndex):
            self.activated.emit(
                self.popup().model().data(
                    self.popup().model().index(idx.row(), 1)
                )
            )
        # TODO: implement conversion from app_name to app_title (signal loop here)
        # if isinstance(idx_str, str):
        #     self.activated.emit(idx_str)


class ImportGroup(QGroupBox, Ui_ImportGroup):
    def __init__(self, parent=None):
        super(ImportGroup, self).__init__(parent=parent)
        self.setupUi(self)
        self.core = shared.core
        self.app_name_list = [game.app_name for game in shared.api_results.game_list]
        self.install_dir_list = [
            game.metadata.get('customAttributes', {}).get('FolderName', {}).get('value', game.app_name)
            for game in shared.api_results.game_list if not game.is_dlc]

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
            completer=AppNameCompleter(app_names=[(i.app_name, i.app_title) for i in shared.api_results.game_list]),
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
            elif os.path.basename(path) in self.install_dir_list:
                return True, path
        return False, path

    def path_changed(self, path):
        self.info_label.setText(str())
        if self.path_edit.is_valid:
            self.app_name.setText(self.find_app_name(path))
        else:
            self.app_name.setText(str())

    def app_name_edit_cb(self, text) -> Tuple[bool, str]:
        if not text:
            return False, text
        if text in self.app_name_list:
            return True, text
        else:
            return False, text

    def app_name_changed(self, text):
        self.info_label.setText(str())
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
                return json.load(open(file, "r")).get("AppName")
        else:
            logger.warning("File was not found")
            return None

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

        if not (err := legendary_utils.import_game(self.core, app_name=app_name, path=path)):
            igame = self.core.get_installed_game(app_name)
            self.info_label.setText(self.tr("Successfully imported {}").format(igame.title))
            self.app_name.setText(str())
            shared.signals.update_gamelist.emit([app_name])

            if igame.version != self.core.get_asset(app_name, igame.platform, False).build_version:
                # update available
                shared.signals.add_download.emit(igame.app_name)
                shared.signals.update_download_tab_text.emit()

        else:
            logger.warning(f'Failed to import "{app_name}"')
            self.info_label.setText(self.tr("Could not import {}: ").format(app_name) + err)
            return

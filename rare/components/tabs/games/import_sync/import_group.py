import json
import os
from logging import getLogger
from pathlib import Path
from typing import List, Tuple, Optional

from PyQt5.QtCore import Qt, QModelIndex, pyqtSignal
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QFileDialog, QGroupBox, QCompleter, QTreeView, QHeaderView

from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton, ApiResultsSingleton
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
            self.activated.emit(self.popup().model().data(self.popup().model().index(idx.row(), 1)))
        # TODO: implement conversion from app_name to app_title (signal loop here)
        # if isinstance(idx_str, str):
        #     self.activated.emit(idx_str)


class ImportGroup(QGroupBox):
    def __init__(self, parent=None):
        super(ImportGroup, self).__init__(parent=parent)
        self.ui = Ui_ImportGroup()
        self.ui.setupUi(self)
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()
        self.api_results = ApiResultsSingleton()

        self.app_name_list = [game.app_name for game in self.api_results.game_list]
        self.install_dir_list = [
            game.metadata.get("customAttributes", {})
            .get("FolderName", {})
            .get("value", game.app_name)
            for game in self.api_results.game_list
            if not game.is_dlc
        ]

        self.path_edit = PathEdit(
            self.core.get_default_install_dir(),
            QFileDialog.DirectoryOnly,
            edit_func=self.path_edit_cb,
            parent=self,
        )
        self.path_edit.textChanged.connect(self.path_changed)
        self.ui.path_edit_layout.addWidget(self.path_edit)

        self.app_name_edit = IndicatorLineEdit(
            placeholder=self.tr("Use in case the app name was not found automatically"),
            completer=AppNameCompleter(
                app_names=[(i.app_name, i.app_title) for i in self.api_results.game_list]
            ),
            edit_func=self.app_name_edit_cb,
            parent=self,
        )
        self.app_name_edit.textChanged.connect(self.app_name_changed)
        self.ui.app_name_layout.addWidget(self.app_name_edit)

        self.ui.import_button.setEnabled(False)
        self.ui.import_button.clicked.connect(
            lambda: self.import_games(self.path_edit.text())
            if self.ui.import_folder_check.isChecked()
            else self.import_game(self.path_edit.text())
        )

        self.ui.import_folder_check.stateChanged.connect(
            lambda s: self.ui.import_button.setEnabled(s or (not s and self.app_name_edit.is_valid))
        )
        self.ui.import_folder_check.stateChanged.connect(
            lambda s: self.app_name_edit.setEnabled(not s)
        )

    def path_edit_cb(self, path) -> Tuple[bool, str, str]:
        if os.path.exists(path):
            if os.path.exists(os.path.join(path, ".egstore")):
                return True, path, ""
            elif os.path.basename(path) in self.install_dir_list:
                return True, path, ""
        else:
            return False, path, PathEdit.reasons.dir_not_exist
        return False, path, ""

    def path_changed(self, path):
        self.ui.info_label.setText(str())
        self.ui.import_folder_check.setChecked(False)
        if self.path_edit.is_valid:
            self.app_name_edit.setText(self.find_app_name(path))
        else:
            self.app_name_edit.setText(str())

    def app_name_edit_cb(self, text) -> Tuple[bool, str, str]:
        if not text:
            return False, text, ""
        if text in self.app_name_list:
            return True, text, ""
        else:
            return False, text, IndicatorLineEdit.reasons.game_not_installed

    def app_name_changed(self, text):
        self.ui.info_label.setText(str())
        if self.app_name_edit.is_valid:
            self.ui.import_button.setEnabled(True)
        else:
            self.ui.import_button.setEnabled(False)

    def find_app_name(self, path: str) -> Optional[str]:
        if os.path.exists(os.path.join(path, ".egstore")):
            for i in os.listdir(os.path.join(path, ".egstore")):
                if i.endswith(".mancpn"):
                    file = os.path.join(path, ".egstore", i)
                    return json.load(open(file, "r")).get("AppName")
        elif app_name := legendary_utils.resolve_aliases(
                self.core, os.path.basename(os.path.normpath(path))):
            return app_name
        else:
            logger.warning(f"Could not find AppName for {path}")
        return None

    def import_game(self, path=None):
        if not path:
            path = self.path_edit.text()
        if not (app_name := self.app_name_edit.text()):
            # try to find app name
            if a_n := self.find_app_name(path):
                app_name = a_n
            else:
                self.ui.info_label.setText(self.tr("Could not find AppName"))
                return
        self.__import_game(app_name, path)

    def import_games(self, path=None):
        if not path:
            path = self.path_edit.text()
        path = Path(path)
        for child in path.iterdir():
            if child.is_dir():
                if (app_name := self.find_app_name(str(child))) is not None:
                    self.__import_game(app_name, str(child))

    def __import_game(self, app_name, path):
        if not (err := legendary_utils.import_game(self.core, app_name=app_name, path=path)):
            igame = self.core.get_installed_game(app_name)
            logger.info(f"Successfully imported {igame.title}")
            self.ui.info_label.setText(self.tr("Successfully imported {}").format(igame.title))
            self.signals.update_gamelist.emit([app_name])

            if igame.version != self.core.get_asset(app_name, igame.platform, False).build_version:
                # update available
                self.signals.add_download.emit(igame.app_name)
                self.signals.update_download_tab_text.emit()

        else:
            logger.warning(f'Failed to import "{app_name}"')
            self.ui.info_label.setText(self.tr("Could not import {}: {}").format(app_name, err))
            return

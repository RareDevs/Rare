import os
import platform
from glob import glob
from typing import Tuple
from logging import getLogger

from PyQt5.QtCore import Qt, QThread
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QGroupBox, \
    QCheckBox, QPushButton, QListWidgetItem, QDialog, QFileDialog, QSizePolicy

import rare.shared as shared
from rare.ui.components.tabs.games.import_sync.egl_sync_widget import Ui_EGLSyncGroup
from rare.utils.extra_widgets import PathEdit
from rare.utils.utils import WineResolver
from rare.utils.models import PathSpec

logger = getLogger("EGLSync")


class EGLSyncGroup(QGroupBox, Ui_EGLSyncGroup):
    importable_items = list()
    exportable_items = list()
    wine_resolver: QThread

    def __init__(self, parent=None):
        super(EGLSyncGroup, self).__init__(parent=parent)
        self.setupUi(self)
        self.export_list.setProperty("noBorder", 1)
        self.import_list.setProperty("noBorder", 1)

        self.core = shared.core

        if platform.system() == "Windows":
            estimated_path = os.path.expandvars(PathSpec.egl_programdata)
        else:
            estimated_path = str()
            self.wine_resolver = WineResolver(PathSpec.egl_programdata, 'default', shared.core)
            self.wine_resolver.result_ready.connect(self.egl_path_info.setText)
            self.wine_resolver.finished.connect(self.wine_resolver.quit)
            self.wine_resolver.finished.connect(self.wine_resolver.deleteLater)
            self.wine_resolver.start()
        self.egl_path_info.setText(estimated_path)

        # if shared.core.egl.programdata_path:

        # if platform.system() != "Windows":
        #     shared.core.lgd.config.set('Legendary', 'egl_programdata', egl_path)
        #     shared.core.egl.programdata_path = egl_path
        #
        # egl_path = os.path.expanduser("~/")
        # if egl_path := shared.core.egl.programdata_path:
        #     pass
        # elif egl_path := shared.core.lgd.config.get("default", "wine_prefix", fallback=""):
        #     egl_data_path = os.path.join(
        #         shared.core.lgd.config.get("default", "wine_prefix", fallback=""),
        #         'drive_c/ProgramData/Epic/EpicGamesLauncher/Data')
        #     egl_path = os.path.join(egl_data_path, 'Manifests')
        # else:
        #     possible_wine_prefixes = [os.path.expanduser("~/.wine"),
        #                               os.path.expanduser("~/Games/epic-games-store")]
        #     for i in possible_wine_prefixes:
        #         if os.path.exists(p := os.path.join(i, "drive_c/ProgramData/Epic/EpicGamesLauncher/Data/Manifests")):
        #             egl_path = p

        if platform.system() != "Windows":
            egl_path = self.core.egl.programdata_path
            if egl_path is None:
                egl_path = str()
            self.egl_path_edit = PathEdit(
                path=egl_path,
                ph_text=estimated_path,
                file_type=QFileDialog.DirectoryOnly,
                edit_func=self.egl_path_edit_cb,
                save_func=self.egl_path_save_cb,
                parent=self
            )
            self.egl_path_edit.textChanged.connect(self.egl_path_changed)
            self.egl_path_layout.addWidget(self.egl_path_edit)
        else:
            self.egl_path_label.setVisible(False)

        self.egl_sync_check.setChecked(shared.core.egl_sync_enabled)
        self.egl_sync_check.stateChanged.connect(self.egl_sync_changed)

        self.export_list.itemDoubleClicked.connect(
            lambda item:
            item.setCheckState(Qt.Unchecked) if item.checkState() != Qt.Unchecked else item.setCheckState(Qt.Checked))
        self.import_list.itemDoubleClicked.connect(
            lambda item:
            item.setCheckState(Qt.Unchecked) if item.checkState() != Qt.Unchecked else item.setCheckState(Qt.Checked))

        self.export_select_all_button.clicked.connect(
            lambda: self.select_items(self.exportable_items, Qt.Checked))
        self.export_select_none_button.clicked.connect(
            lambda: self.select_items(self.exportable_items, Qt.Unchecked))
        self.import_select_all_button.clicked.connect(
            lambda: self.select_items(self.importable_items, Qt.Checked))
        self.import_select_none_button.clicked.connect(
            lambda: self.select_items(self.importable_items, Qt.Unchecked))

        self.export_button.clicked.connect(self.export_selected)
        self.import_button.clicked.connect(self.import_selected)

        self.update_lists()

    @staticmethod
    def egl_path_edit_cb(path) -> Tuple[bool, str]:
        if not path:
            return True, path
        if platform.system() != "Windows":
            path = path.rstrip('/')
            if os.path.exists(os.path.join(path, 'system.reg')) and os.path.exists(os.path.join(path, 'dosdevices/c:')):
                # path is a wine prefix
                path = os.path.join(path, 'dosdevices/c:', 'ProgramData/Epic/EpicGamesLauncher/Data/Manifests')
            elif not path.endswith('ProgramData/Epic/EpicGamesLauncher/Data/Manifests'):
                # lower() might or might not be needed in the check
                return False, path
        if os.path.exists(path):
            return True, path
        return False, path

    def egl_path_save_cb(self, path):
        if not path:
            # This is the same as "--unlink"
            self.core.egl.programdata_path = None
            self.core.lgd.config.remove_option('Legendary', 'egl_programdata')
            self.core.lgd.config.remove_option('Legendary', 'egl_sync')
            # remove EGL GUIDs from all games, DO NOT remove .egstore folders because that would fuck things up.
            for igame in self.core.get_installed_list():
                igame.egl_guid = ''
                self.core.install_game(igame)
        else:
            self.core.egl.programdata_path = path
            self.core.lgd.config.set("Legendary", "egl_programdata", path)
        self.core.lgd.save_config()

    def egl_path_changed(self, path):
        if self.egl_path_edit.is_valid:
            self.egl_sync_check.setEnabled(bool(path))
            self.egl_sync_check.setCheckState(Qt.Unchecked)
            self.update_lists()

    def egl_sync_changed(self, state):
        if state == Qt.Unchecked:
            self.core.lgd.config.remove_option('Legendary', 'egl_sync')
        else:
            self.core.lgd.config.set('Legendary', 'egl_sync', str(True))
            self.core.egl_sync()
            self.update_lists()
        self.core.lgd.save_config()

    def update_lists(self):
        have_path = bool(shared.core.egl.programdata_path)
        self.egl_sync_label.setEnabled(have_path)
        self.egl_sync_check.setEnabled(have_path)

        self.export_import_widget.setEnabled(have_path)

        self.export_label.setVisible(not have_path)
        self.export_list.setVisible(have_path)
        self.export_buttons_widget.setVisible(have_path)

        self.import_label.setVisible(not have_path)
        self.import_list.setVisible(have_path)
        self.import_buttons_widget.setVisible(have_path)

        if not have_path:
            return

        self.update_export_list()
        self.update_import_list()

    def update_export_list(self):
        self.export_list.clear()
        self.exportable_items.clear()
        exportable_games = shared.core.egl_get_exportable()
        for igame in exportable_games:
            ew = EGLSyncItem(igame, True, self.export_list)
            self.exportable_items.append(ew)
            self.export_list.addItem(ew)
        have_exportable = bool(exportable_games)
        self.export_label.setVisible(not have_exportable)
        self.export_list.setVisible(have_exportable)
        self.export_buttons_widget.setVisible(have_exportable)

    def update_import_list(self):
        self.import_list.clear()
        self.importable_items.clear()
        importable_games = shared.core.egl_get_importable()
        for game in importable_games:
            iw = EGLSyncItem(game, False, self.import_list)
            self.importable_items.append(iw)
            self.import_list.addItem(iw)
        have_importable = bool(importable_games)
        self.import_label.setVisible(not have_importable)
        self.import_list.setVisible(have_importable)
        self.import_buttons_widget.setVisible(have_importable)

    @staticmethod
    def select_items(item_list, state):
        for w in item_list:
            w.setCheckState(state)

    def export_selected(self):
        for ew in self.exportable_items:
            if ew.is_checked():
                ew.export_game()
                self.export_list.takeItem(self.export_list.row(ew))
        self.update_export_list()

    def import_selected(self):
        for iw in self.importable_items:
            if iw.is_checked:
                iw.import_game()
                self.import_list.takeItem(self.import_list.row(iw))
        self.update_import_list()


class EGLSyncItem(QListWidgetItem):
    def __init__(self, game, export: bool, parent=None):
        super(EGLSyncItem, self).__init__(parent=parent)
        self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        self.setCheckState(Qt.Unchecked)
        self.game = game
        self.export = export
        if export:
            self.setText(game.title)
        else:
            self.setText(shared.core.get_game(game.app_name).app_title)

    def is_checked(self):
        return True if self.checkState() == Qt.Checked else False

    def export_game(self):
        shared.core.egl_export(self.game.app_name)

    def import_game(self):
        shared.core.egl_import(self.game.app_name)


class DisableSyncDialog(QDialog):
    info = 1, False

    def __init__(self, parent=None):
        super(DisableSyncDialog, self).__init__(parent=parent)
        self.layout = QVBoxLayout()

        self.question = QLabel(self.tr("Do you really want to disable sync with Epic Games Store"))
        self.layout.addWidget(self.question)

        self.remove_metadata = QCheckBox(self.tr("Remove metadata from installed games"))
        self.layout.addWidget(self.remove_metadata)

        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch(1)

        self.ok_button = QPushButton(self.tr("Ok"))
        self.cancel_button = QPushButton(self.tr("Cancel"))

        self.ok_button.clicked.connect(self.ok)
        self.cancel_button.clicked.connect(self.cancel)

        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.cancel_button)

        self.layout.addStretch(1)
        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)

    def ok(self):
        self.info = 0, self.remove_metadata.isChecked()
        self.close()

    def cancel(self):
        self.close()

    def get_information(self):
        self.exec_()
        return self.info


class EGLSyncItemWidget(QGroupBox):
    def __init__(self, game, export: bool, parent=None):
        super(EGLSyncItemWidget, self).__init__(parent=parent)
        self.layout = QHBoxLayout()
        self.export = export
        self.game = game
        if export:
            self.app_title_label = QLabel(game.title)
        else:
            title = shared.core.get_game(game.app_name).app_title
            self.app_title_label = QLabel(title)
        self.layout.addWidget(self.app_title_label)
        self.button = QPushButton(self.tr("Export") if export else self.tr("Import"))

        if export:
            self.button.clicked.connect(self.export_game)
        else:
            self.button.clicked.connect(self.import_game)

        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

    def export_game(self):
        shared.core.egl_export(self.game.app_name)
        # FIXME: on update_egl_widget this is going to crash because
        # FIXME: the item is not removed from the list in the python's side
        self.deleteLater()

    def import_game(self):
        shared.core.egl_import(self.game.app_name)
        # FIXME: on update_egl_widget this is going to crash because
        # FIXME: the item is not removed from the list in the python's side
        self.deleteLater()

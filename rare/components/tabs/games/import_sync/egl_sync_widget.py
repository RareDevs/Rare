import os
import platform
from logging import getLogger

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QGroupBox, \
    QCheckBox, QPushButton, QListWidgetItem, QDialog, QFileDialog

import rare.shared as shared
from rare.ui.components.tabs.games.import_sync.egl_sync_widget import Ui_EGLSyncGroup
from rare.utils.extra_widgets import PathEdit

logger = getLogger("EGLSync")


class EGLSyncGroup(QGroupBox, Ui_EGLSyncGroup):
    importable_items = list()
    exportable_items = list()

    def __init__(self, parent=None):
        super(EGLSyncGroup, self).__init__(parent=parent)
        self.setupUi(self)

        self.egl_path_info.setText(
            self.tr("EGL path is at C:\\ProgramData\\Epic\\EpicGamesLauncher\\Data\\Manifests"))
        egl_path = os.path.expanduser("~/")
        if egl_path := shared.legendary_core.egl.programdata_path:
            pass
        elif egl_path := shared.legendary_core.lgd.config.get("default", "wine_prefix", fallback=""):
            egl_data_path = os.path.join(shared.legendary_core.lgd.config.get("default", "wine_prefix", fallback=""),
                                         'drive_c/ProgramData/Epic/EpicGamesLauncher/Data')
            egl_path = os.path.join(egl_data_path, 'Manifests')
        else:
            possible_wine_prefixes = [os.path.expanduser("~/.wine"),
                                      os.path.expanduser("~/Games/epic-games-store")]
            for i in possible_wine_prefixes:
                if os.path.exists(p := os.path.join(i, "drive_c/ProgramData/Epic/EpicGamesLauncher/Data/Manifests")):
                    egl_path = p

        self.egl_path_edit = PathEdit(egl_path, QFileDialog.DirectoryOnly, save_func=self.save_egl_path)
        self.egl_path_layout.addWidget(self.egl_path_edit)
        if platform.system() != "Windows":
            shared.legendary_core.lgd.config.set('Legendary', 'egl_programdata', egl_path)
            shared.legendary_core.egl.programdata_path = egl_path

        if shared.legendary_core.egl_sync_enabled:
            self.refresh_button.setText(self.tr("Disable sync"))
        else:
            self.refresh_button.setText(self.tr("Enable Sync"))
        self.refresh_button.clicked.connect(self.sync)

        # self.enable_sync_button.clicked.connect(self.enable_sync)
        # self.sync_once_button.clicked.connect(shared.lgd_core.egl_sync)

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

    def check_egl_path(self, path):
        pass

    def save_egl_path(self):
        shared.legendary_core.lgd.config.set("Legendary", "egl_programdata", self.egl_path_edit.text())
        shared.legendary_core.egl.programdata_path = self.egl_path_edit.text()
        shared.legendary_core.lgd.save_config()
        self.update_lists()

    def update_export_list(self):
        self.export_button.setDisabled(not bool(shared.legendary_core.egl.programdata_path))
        self.export_select_all_button.setDisabled(not bool(shared.legendary_core.egl.programdata_path))
        self.export_select_none_button.setDisabled(not bool(shared.legendary_core.egl.programdata_path))

        self.export_list.clear()
        self.exportable_items.clear()
        exportable_games = shared.legendary_core.egl_get_exportable()
        for igame in exportable_games:
            ew = EGLSyncItem(igame, True, self.export_list)
            self.exportable_items.append(ew)
            self.export_list.addItem(ew)
        self.export_group.setEnabled(bool(exportable_games))
        self.export_button.setEnabled(bool(exportable_games))
        self.export_label.setVisible(not bool(exportable_games))

    def update_import_list(self):
        self.import_button.setDisabled(not bool(shared.legendary_core.egl.programdata_path))
        self.import_select_all_button.setDisabled(not bool(shared.legendary_core.egl.programdata_path))
        self.import_select_none_button.setDisabled(not bool(shared.legendary_core.egl.programdata_path))

        self.import_list.clear()
        self.importable_items.clear()
        importable_games = shared.legendary_core.egl_get_importable()
        for game in importable_games:
            iw = EGLSyncItem(game, False, self.import_list)
            self.importable_items.append(iw)
            self.import_list.addItem(iw)
        self.import_group.setEnabled(bool(importable_games))
        self.import_button.setEnabled(bool(importable_games))
        self.import_label.setVisible(not bool(importable_games))

    def update_lists(self):
        self.export_list.setVisible(bool(shared.legendary_core.egl.programdata_path))
        self.import_list.setVisible(bool(shared.legendary_core.egl.programdata_path))
        if not shared.legendary_core.egl.programdata_path:
            return
        self.update_export_list()
        self.update_import_list()

    def enable_sync(self):
        if not shared.legendary_core.egl.programdata_path:
            if os.path.exists(path := self.egl_path_edit.text()):
                shared.legendary_core.lgd.config.set("Legendary", "egl_programdata", path)
                shared.legendary_core.lgd.save_config()
                shared.legendary_core.egl.programdata_path = path

        shared.legendary_core.lgd.config.set('Legendary', 'egl_sync', "true")
        shared.legendary_core.egl_sync()
        shared.legendary_core.lgd.save_config()
        self.refresh_button.setText(self.tr("Disable Sync"))
        self.enable_sync_button.setDisabled(True)

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

    def sync(self):
        if shared.legendary_core.egl_sync_enabled:
            # disable sync
            info = DisableSyncDialog().get_information()
            if info[0] == 0:
                if info[1]:
                    shared.legendary_core.lgd.config.remove_option('Legendary', 'egl_sync')
                else:
                    shared.legendary_core.lgd.config.remove_option('Legendary', 'egl_programdata')
                    shared.legendary_core.lgd.config.remove_option('Legendary', 'egl_sync')
                    # remove EGL GUIDs from all games, DO NOT remove .egstore folders because that would fuck things up.
                    for igame in shared.legendary_core.get_installed_list():
                        igame.egl_guid = ''
                        shared.legendary_core.install_game(igame)
                shared.legendary_core.lgd.save_config()
                self.refresh_button.setText(self.tr("Enable Sync"))
        else:
            # enable sync
            # self.enable_sync_button.setDisabled(False)
            self.update_lists()


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
            self.setText(shared.legendary_core.get_game(game.app_name).app_title)

    def is_checked(self):
        return True if self.checkState() == Qt.Checked else False

    def export_game(self):
        shared.legendary_core.egl_export(self.game.app_name)

    def import_game(self):
        shared.legendary_core.egl_import(self.game.app_name)


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
            title = shared.legendary_core.get_game(game.app_name).app_title
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
        shared.legendary_core.egl_export(self.game.app_name)
        # FIXME: on update_egl_widget this is going to crash because
        # FIXME: the item is not removed from the list in the python's side
        self.deleteLater()

    def import_game(self):
        shared.legendary_core.egl_import(self.game.app_name)
        # FIXME: on update_egl_widget this is going to crash because
        # FIXME: the item is not removed from the list in the python's side
        self.deleteLater()

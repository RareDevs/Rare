import os
import platform
from logging import getLogger
from typing import List, Tuple

from PyQt5.QtCore import Qt, QThread, QFileSystemWatcher
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QGroupBox, \
    QCheckBox, QPushButton, QListWidgetItem, QDialog, QFileDialog

import rare.shared as shared
from rare.ui.components.tabs.games.import_sync.egl_sync_group import Ui_EGLSyncGroup
from rare.ui.components.tabs.games.import_sync.egl_sync_list_group import Ui_EGLSyncListGroup
from rare.utils.extra_widgets import PathEdit
from rare.utils.models import PathSpec
from rare.utils.utils import WineResolver

logger = getLogger("EGLSync")


class EGLSyncGroup(QGroupBox, Ui_EGLSyncGroup):
    wine_resolver: QThread

    def __init__(self, parent=None):
        super(EGLSyncGroup, self).__init__(parent=parent)
        self.setupUi(self)

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

        egl_path = shared.core.egl.programdata_path
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

        self.egl_watcher = QFileSystemWatcher([self.egl_path_edit.text()], self)
        self.egl_watcher.directoryChanged.connect(self.update_lists)

        if platform.system() == "Windows":
            self.egl_path_label.setVisible(False)
            self.egl_path_edit.setVisible(False)
            self.egl_path_info_label.setVisible(False)
            self.egl_path_info.setVisible(False)

        self.egl_sync_check.setChecked(shared.core.egl_sync_enabled)
        self.egl_sync_check.stateChanged.connect(self.egl_sync_changed)

        self.import_list = EGLSyncListGroup(export=False, parent=self)
        self.import_export_layout.addWidget(self.import_list)
        self.export_list = EGLSyncListGroup(export=True, parent=self)
        self.import_export_layout.addWidget(self.export_list)

        self.update_lists()

    @staticmethod
    def egl_path_edit_cb(path) -> Tuple[bool, str]:
        if not path:
            return True, path
        if platform.system() != "Windows":
            if os.path.exists(os.path.join(path, 'system.reg')) and os.path.exists(os.path.join(path, 'dosdevices/c:')):
                # path is a wine prefix
                path = os.path.join(path, 'dosdevices/c:', 'ProgramData/Epic/EpicGamesLauncher/Data/Manifests')
            elif not path.rstrip('/').endswith('ProgramData/Epic/EpicGamesLauncher/Data/Manifests'):
                # lower() might or might not be needed in the check
                return False, path
        if os.path.exists(path):
            return True, path
        return False, path

    @staticmethod
    def egl_path_save_cb(path):
        if not path:
            # This is the same as "--unlink"
            shared.core.egl.programdata_path = None
            shared.core.lgd.config.remove_option('Legendary', 'egl_programdata')
            shared.core.lgd.config.remove_option('Legendary', 'egl_sync')
            # remove EGL GUIDs from all games, DO NOT remove .egstore folders because that would fuck things up.
            for igame in shared.core.get_installed_list():
                igame.egl_guid = ''
                shared.core.install_game(igame)
        else:
            # NOTE: need to clear known manifests to force refresh
            # shared.core.egl.manifests.clear()
            shared.core.egl.programdata_path = path
            shared.core.lgd.config.set("Legendary", "egl_programdata", path)
        shared.core.lgd.save_config()

    def egl_path_changed(self, path):
        if self.egl_path_edit.is_valid:
            self.egl_sync_check.setEnabled(bool(path))
        self.egl_sync_check.setCheckState(Qt.Unchecked)
        self.egl_watcher.removePaths([p for p in self.egl_watcher.directories()])
        self.egl_watcher.addPaths([path])
        self.update_lists()

    def egl_sync_changed(self, state):
        if state == Qt.Unchecked:
            self.core.lgd.config.remove_option('Legendary', 'egl_sync')
        else:
            self.core.lgd.config.set('Legendary', 'egl_sync', str(True))
            # lk: not sure if this should be done here
            # self.import_list.mark(Qt.Checked)
            # self.import_list.action()
            # self.export_list.mark(Qt.Checked)
            # self.export_list.action()
        self.core.lgd.save_config()

    # def egl_items_changed(self, path: str):
    #     if path == shared.core.egl.programdata_path and self.egl_path_edit.is_valid:
    #         shared.core.egl.manifests.clear()
    #         self.import_list.populate(True)
    #         self.export_list.populate(True)

    def update_lists(self):
        if have_path := bool(shared.core.egl.programdata_path) and self.egl_path_edit.is_valid:
            shared.core.egl.manifests.clear()
        self.egl_sync_label.setEnabled(have_path)
        self.egl_sync_check.setEnabled(have_path)

        self.import_list.populate(have_path)
        self.import_list.setEnabled(have_path)
        self.export_list.populate(have_path)
        self.export_list.setEnabled(have_path)


class EGLSyncListItem(QListWidgetItem):
    def __init__(self, game, export: bool, parent=None):
        super(EGLSyncListItem, self).__init__(parent=parent)
        self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        self.setCheckState(Qt.Unchecked)
        self.game = game
        self.export = export
        if export:
            self.setText(game.title)
        else:
            self.setText(shared.core.get_game(game.app_name).app_title)

    def is_checked(self) -> bool:
        return True if self.checkState() == Qt.Checked else False

    def action(self) -> None:
        if self.export:
            shared.core.egl_export(self.game.app_name)
        else:
            shared.core.egl_import(self.game.app_name)


class EGLSyncListGroup(QGroupBox, Ui_EGLSyncListGroup):

    def __init__(self, export: bool, parent=None):
        super(EGLSyncListGroup, self).__init__(parent=parent)
        self.setupUi(self)
        self.list.setProperty("noBorder", 1)

        self.export = export

        if export:
            self.setTitle(self.tr('Exportable games'))
            self.label.setText(self.tr('No games to export to EGL'))
            self.action_button.setText(self.tr('Export'))
            self.list_func = shared.core.egl_get_exportable
        else:
            self.setTitle(self.tr('Importable games'))
            self.label.setText(self.tr('No games to import from EGL'))
            self.action_button.setText(self.tr('Import'))
            self.list_func = shared.core.egl_get_importable

        self.list.itemDoubleClicked.connect(
            lambda item:
            item.setCheckState(Qt.Unchecked) if item.checkState() != Qt.Unchecked else item.setCheckState(Qt.Checked)
        )

        self.select_all_button.clicked.connect(lambda: self.mark(Qt.Checked))
        self.select_none_button.clicked.connect(lambda: self.mark(Qt.Unchecked))

        self.action_button.clicked.connect(self.action)

    def mark(self, state):
        for item in self.items:
            item.setCheckState(state)

    def populate(self, enabled: bool):
        if enabled:
            self.list.clear()
            for item in self.list_func():
                self.list.addItem(EGLSyncListItem(item, self.export, self.list))
        self.label.setVisible(not enabled or not bool(self.list.count()))
        self.list.setVisible(enabled and bool(self.list.count()))
        self.buttons_widget.setVisible(enabled and bool(self.list.count()))

    def action(self):
        for item in self.items:
            if item.is_checked():
                item.action()
                self.list.takeItem(self.list.row(item))
        shared.signals.update_gamelist.emit(str())
        self.populate(True)

    @property
    def items(self) -> List[EGLSyncListItem]:
        return [self.list.item(i) for i in range(self.list.count())]


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

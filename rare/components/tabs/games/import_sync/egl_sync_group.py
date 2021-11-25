import os
import platform
from logging import getLogger
from typing import Tuple, Iterable

from PyQt5.QtCore import Qt, QThreadPool, QRunnable, pyqtSlot
from PyQt5.QtWidgets import QGroupBox, QListWidgetItem, QFileDialog, QMessageBox

import rare.shared as shared
from rare.ui.components.tabs.games.import_sync.egl_sync_group import Ui_EGLSyncGroup
from rare.ui.components.tabs.games.import_sync.egl_sync_list_group import Ui_EGLSyncListGroup
from rare.utils.extra_widgets import PathEdit
from rare.utils.models import PathSpec
from rare.utils.utils import WineResolver

logger = getLogger("EGLSync")


class EGLSyncGroup(QGroupBox, Ui_EGLSyncGroup):

    def __init__(self, parent=None):
        super(EGLSyncGroup, self).__init__(parent=parent)
        self.setupUi(self)
        self.egl_path_info.setProperty('infoLabel', 1)

        self.thread_pool = QThreadPool.globalInstance()

        if platform.system() == 'Windows':
            self.egl_path_edit_label.setVisible(False)
            self.egl_path_info_label.setVisible(False)
            self.egl_path_info.setVisible(False)
        else:
            self.egl_path_edit = PathEdit(
                path=shared.core.egl.programdata_path,
                ph_text=self.tr('Path to the Wine prefix where EGL is installed, or the Manifests folder'),
                file_type=QFileDialog.DirectoryOnly,
                edit_func=self.egl_path_edit_edit_cb,
                save_func=self.egl_path_edit_save_cb,
                parent=self
            )
            self.egl_path_edit.textChanged.connect(self.egl_path_changed)
            self.egl_path_edit_layout.addWidget(self.egl_path_edit)

            if not shared.core.egl.programdata_path:
                self.egl_path_info.setText(self.tr('Updating...'))
                wine_resolver = WineResolver(PathSpec.egl_programdata, 'default', shared.core)
                wine_resolver.signals.result_ready.connect(self.wine_resolver_cb)
                self.thread_pool.start(wine_resolver)
            else:
                self.egl_path_info_label.setVisible(False)
                self.egl_path_info.setVisible(False)

        self.egl_sync_check.setChecked(shared.core.egl_sync_enabled)
        self.egl_sync_check.stateChanged.connect(self.egl_sync_changed)

        self.import_list = EGLSyncListGroup(export=False, parent=self)
        self.import_export_layout.addWidget(self.import_list)
        self.export_list = EGLSyncListGroup(export=True, parent=self)
        self.import_export_layout.addWidget(self.export_list)

        # self.egl_watcher = QFileSystemWatcher([self.egl_path_edit.text()], self)
        # self.egl_watcher.directoryChanged.connect(self.update_lists)

        self.update_lists()

    def wine_resolver_cb(self, path):
        self.egl_path_info.setText(path)
        if not path:
            self.egl_path_info.setText(
                self.tr('Default Wine prefix is unset, or path does not exist. '
                        'Create it or configure it in Settings -> Linux.'))
        elif not os.path.exists(path):
            self.egl_path_info.setText(
                self.tr('Default Wine prefix is set but EGL manifests path does not exist. '
                        'Your configured default Wine prefix might not be where EGL is installed.'))
        else:
            self.egl_path_edit.setText(path)

    @staticmethod
    def egl_path_edit_edit_cb(path) -> Tuple[bool, str]:
        if not path:
            return True, path
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
    def egl_path_edit_save_cb(path):
        if not path or not os.path.exists(path):
            # This is the same as "--unlink"
            shared.core.egl.programdata_path = None
            shared.core.lgd.config.remove_option('Legendary', 'egl_programdata')
            shared.core.lgd.config.remove_option('Legendary', 'egl_sync')
            # remove EGL GUIDs from all games, DO NOT remove .egstore folders because that would fuck things up.
            for igame in shared.core.get_installed_list():
                igame.egl_guid = ''
                shared.core.install_game(igame)
        else:
            shared.core.egl.programdata_path = path
            shared.core.lgd.config.set("Legendary", "egl_programdata", path)

        shared.core.lgd.save_config()

    def egl_path_changed(self, path):
        if self.egl_path_edit.is_valid:
            self.egl_sync_check.setEnabled(bool(path))
        self.egl_sync_check.setCheckState(Qt.Unchecked)
        # self.egl_watcher.removePaths([p for p in self.egl_watcher.directories()])
        # self.egl_watcher.addPaths([path])
        self.update_lists()

    def egl_sync_changed(self, state):
        if state == Qt.Unchecked:
            self.import_list.setEnabled(bool(self.import_list.items))
            self.export_list.setEnabled(bool(self.export_list.items))
            shared.core.lgd.config.remove_option('Legendary', 'egl_sync')
        else:
            shared.core.lgd.config.set('Legendary', 'egl_sync', str(True))
            # lk: do import/export here since automatic sync was selected
            self.import_list.mark(Qt.Checked)
            self.export_list.mark(Qt.Checked)
            sync_worker = EGLSyncWorker(self.import_list, self.export_list)
            self.thread_pool.start(sync_worker)
            self.import_list.setEnabled(False)
            self.export_list.setEnabled(False)
            # self.update_lists()
        shared.core.lgd.save_config()

    def update_lists(self):
        # self.egl_watcher.blockSignals(True)
        if have_path := bool(shared.core.egl.programdata_path) and os.path.exists(shared.core.egl.programdata_path):
            # NOTE: need to clear known manifests to force refresh
            shared.core.egl.manifests.clear()
        self.egl_sync_check_label.setEnabled(have_path)
        self.egl_sync_check.setEnabled(have_path)
        self.import_list.populate(have_path)
        self.import_list.setEnabled(have_path)
        self.export_list.populate(have_path)
        self.export_list.setEnabled(have_path)
        # self.egl_watcher.blockSignals(False)


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
            error = shared.core.egl_export(self.game.app_name)
        else:
            error = shared.core.egl_import(self.game.app_name)
        return error

    @property
    def app_name(self):
        return self.game.app_name

    @property
    def app_title(self):
        return self.game.app_title


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
        self.list.itemChanged.connect(self.has_selected)

        self.select_all_button.clicked.connect(lambda: self.mark(Qt.Checked))
        self.select_none_button.clicked.connect(lambda: self.mark(Qt.Unchecked))

        self.action_button.clicked.connect(self.action)

    def has_selected(self):
        for item in self.items:
            if item.is_checked():
                self.action_button.setEnabled(True)
                return
        self.action_button.setEnabled(False)

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
        imported = list()
        errors = list()
        for item in self.items:
            if item.is_checked():
                if e := item.action():
                    errors.append(e)
                else:
                    imported.append(item.app_name)
                    self.list.takeItem(self.list.row(item))
        if not self.export and imported:
            shared.signals.update_gamelist.emit(imported)
        self.populate(True)
        if errors:
            QMessageBox.warning(
                self.parent(),
                self.tr('The following errors occurred while {}.').format(
                    self.tr('exporting') if self.export else self.tr('importing')),
                '\n'.join(errors)
            )

    @property
    def items(self) -> Iterable[EGLSyncListItem]:
        # for i in range(self.list.count()):
        #     yield self.list.item(i)
        return [self.list.item(i) for i in range(self.list.count())]


class EGLSyncWorker(QRunnable):
    def __init__(self, import_list: EGLSyncListGroup, export_list: EGLSyncListGroup):
        super(EGLSyncWorker, self).__init__()
        self.setAutoDelete(True)
        self.import_list = import_list
        self.export_list = export_list

    @pyqtSlot()
    def run(self):
        self.import_list.action()
        self.export_list.action()


'''
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QCheckBox, QPushButton, QDialog


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
'''

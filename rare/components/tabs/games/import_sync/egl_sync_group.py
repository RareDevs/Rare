import os
import platform
from logging import getLogger
from typing import Tuple, Iterable, List

from PyQt5.QtCore import Qt, QThreadPool, QRunnable, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QGroupBox, QListWidgetItem, QFileDialog, QMessageBox

from rare.lgndr.api_exception import LgndrException
from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton
from rare.ui.components.tabs.games.import_sync.egl_sync_group import Ui_EGLSyncGroup
from rare.ui.components.tabs.games.import_sync.egl_sync_list_group import (
    Ui_EGLSyncListGroup,
)
from rare.utils.extra_widgets import PathEdit
from rare.utils.models import PathSpec
from rare.utils.misc import WineResolver

logger = getLogger("EGLSync")


class EGLSyncGroup(QGroupBox, Ui_EGLSyncGroup):
    def __init__(self, parent=None):
        super(EGLSyncGroup, self).__init__(parent=parent)
        self.setupUi(self)
        self.core = LegendaryCoreSingleton()
        self.egl_path_info.setProperty("infoLabel", 1)

        self.thread_pool = QThreadPool.globalInstance()

        if platform.system() == "Windows":
            self.egl_path_edit_label.setVisible(False)
            self.egl_path_info_label.setVisible(False)
            self.egl_path_info.setVisible(False)
        else:
            self.egl_path_edit = PathEdit(
                path=self.core.egl.programdata_path,
                placeholder=self.tr(
                    "Path to the Wine prefix where EGL is installed, or the Manifests folder"
                ),
                file_type=QFileDialog.DirectoryOnly,
                edit_func=self.egl_path_edit_edit_cb,
                save_func=self.egl_path_edit_save_cb,
                parent=self,
            )
            self.egl_path_edit.textChanged.connect(self.egl_path_changed)
            self.egl_path_edit_layout.addWidget(self.egl_path_edit)

            if not self.core.egl.programdata_path:
                self.egl_path_info.setText(self.tr("Updating..."))
                wine_resolver = WineResolver(
                    PathSpec.egl_programdata, "default"
                )
                wine_resolver.signals.result_ready.connect(self.wine_resolver_cb)
                self.thread_pool.start(wine_resolver)
            else:
                self.egl_path_info_label.setVisible(False)
                self.egl_path_info.setVisible(False)

        self.egl_sync_check.setChecked(self.core.egl_sync_enabled)
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
                self.tr(
                    "Default Wine prefix is unset, or path does not exist. "
                    "Create it or configure it in Settings -> Linux."
                )
            )
        elif not os.path.exists(path):
            self.egl_path_info.setText(
                self.tr(
                    "Default Wine prefix is set but EGL manifests path does not exist. "
                    "Your configured default Wine prefix might not be where EGL is installed."
                )
            )
        else:
            self.egl_path_edit.setText(path)

    @staticmethod
    def egl_path_edit_edit_cb(path) -> Tuple[bool, str, str]:
        if not path:
            return True, path, ""
        if os.path.exists(os.path.join(path, "system.reg")) and os.path.exists(
                os.path.join(path, "dosdevices/c:")
        ):
            # path is a wine prefix
            path = os.path.join(
                path,
                "dosdevices/c:",
                "ProgramData/Epic/EpicGamesLauncher/Data/Manifests",
            )
        elif not path.rstrip("/").endswith(
                "ProgramData/Epic/EpicGamesLauncher/Data/Manifests"
        ):
            # lower() might or might not be needed in the check
            return False, path, PathEdit.reasons.wrong_path
        if os.path.exists(path):
            return True, path, ""
        return False, path, PathEdit.reasons.dir_not_exist

    def egl_path_edit_save_cb(self, path):
        if not path or not os.path.exists(path):
            # This is the same as "--unlink"
            self.core.egl.programdata_path = None
            self.core.lgd.config.remove_option("Legendary", "egl_programdata")
            self.core.lgd.config.remove_option("Legendary", "egl_sync")
            # remove EGL GUIDs from all games, DO NOT remove .egstore folders because that would fuck things up.
            for igame in self.core.get_installed_list():
                igame.egl_guid = ""
                self.core.install_game(igame)
        else:
            self.core.egl.programdata_path = path
            self.core.lgd.config.set("Legendary", "egl_programdata", path)

        self.core.lgd.save_config()

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
            self.core.lgd.config.remove_option("Legendary", "egl_sync")
        else:
            self.core.lgd.config.set("Legendary", "egl_sync", str(True))
            # lk: do import/export here since automatic sync was selected
            self.import_list.mark(Qt.Checked)
            self.export_list.mark(Qt.Checked)
            sync_worker = EGLSyncWorker(self.import_list, self.export_list)
            self.thread_pool.start(sync_worker)
            self.import_list.setEnabled(False)
            self.export_list.setEnabled(False)
            # self.update_lists()
        self.core.lgd.save_config()

    def update_lists(self):
        # self.egl_watcher.blockSignals(True)
        if have_path := bool(self.core.egl.programdata_path) and os.path.exists(
            self.core.egl.programdata_path
        ):
            # NOTE: need to clear known manifests to force refresh
            self.core.egl.manifests.clear()
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
        self.core = LegendaryCoreSingleton()
        self.game = game
        self.export = export
        if export:
            self.setText(game.title)
        else:  # import
            self.setText(self.core.get_game(game.app_name).app_title)

    def is_checked(self) -> bool:
        return self.checkState() == Qt.Checked

    def action(self) -> str:
        error = ""
        if self.export:
            try:
                self.core.egl_export(self.game.app_name)
            except LgndrException as ret:
                error = ret.message
        else:
            try:
                self.core.egl_import(self.game.app_name)
            except LgndrException as ret:
                error = ret.message
        return error

    @property
    def app_name(self):
        return self.game.app_name

    @property
    def app_title(self):
        return self.game.app_title


class EGLSyncListGroup(QGroupBox, Ui_EGLSyncListGroup):
    action_errors = pyqtSignal(list)

    def __init__(self, export: bool, parent=None):
        super(EGLSyncListGroup, self).__init__(parent=parent)
        self.setupUi(self)
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()
        self.list.setProperty("noBorder", 1)
        # TODO: Convert the CSS and the code to adhere to NoFrame
        # self.list.setFrameShape(self.list.NoFrame)

        self.export = export

        if export:
            self.setTitle(self.tr("Exportable games"))
            self.label.setText(self.tr("No games to export to EGL"))
            self.action_button.setText(self.tr("Export"))
            self.list_func = self.core.egl_get_exportable
        else:
            self.setTitle(self.tr("Importable games"))
            self.label.setText(self.tr("No games to import from EGL"))
            self.action_button.setText(self.tr("Import"))
            self.list_func = self.core.egl_get_importable

        self.list.itemDoubleClicked.connect(
            lambda item: item.setCheckState(Qt.Unchecked)
            if item.checkState() != Qt.Unchecked
            else item.setCheckState(Qt.Checked)
        )
        self.list.itemChanged.connect(self.has_selected)

        self.select_all_button.clicked.connect(lambda: self.mark(Qt.Checked))
        self.select_none_button.clicked.connect(lambda: self.mark(Qt.Unchecked))

        self.action_button.clicked.connect(self.action)

        self.action_errors.connect(self.show_errors)

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
                try:
                    i = EGLSyncListItem(item, self.export, self.list)
                except AttributeError:
                    logger.error(f"{item.app_name} does not work. Ignoring")
                else:
                    self.list.addItem(i)
        self.label.setVisible(not enabled or not bool(self.list.count()))
        self.list.setVisible(enabled and bool(self.list.count()))
        self.buttons_widget.setVisible(enabled and bool(self.list.count()))

    def action(self):
        imported: List = []
        errors: List = []
        for item in self.items:
            if item.is_checked():
                if e := item.action():
                    errors.append(e)
                else:
                    imported.append(item.app_name)
                    self.list.takeItem(self.list.row(item))
        if not self.export and imported:
            self.signals.update_gamelist.emit(imported)
        self.populate(True)
        if errors:
            self.action_errors.emit(errors)

    @pyqtSlot(list)
    def show_errors(self, errors: List):
        QMessageBox.warning(
            self.parent(),
            self.tr("The following errors occurred while {}.").format(
                self.tr("exporting") if self.export else self.tr("importing")
            ),
            "\n".join(errors),
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

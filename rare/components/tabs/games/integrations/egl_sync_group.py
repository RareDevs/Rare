import os
import platform
from abc import abstractmethod
from logging import getLogger
from typing import Tuple, Iterable, List, Union

from PyQt5.QtCore import Qt, QThreadPool, QRunnable, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QGroupBox, QListWidgetItem, QFileDialog, QMessageBox, QFrame, QLabel
from legendary.models.egl import EGLManifest
from legendary.models.game import InstalledGame

from rare.lgndr.glue.exception import LgndrException
from rare.models.pathspec import PathSpec
from rare.shared import RareCore
from rare.shared.workers.wine_resolver import WineResolver
from rare.ui.components.tabs.games.integrations.egl_sync_group import Ui_EGLSyncGroup
from rare.ui.components.tabs.games.integrations.egl_sync_list_group import Ui_EGLSyncListGroup
from rare.widgets.indicator_edit import PathEdit, IndicatorReasonsCommon
from rare.widgets.elide_label import ElideLabel

logger = getLogger("EGLSync")


class EGLSyncGroup(QGroupBox):
    def __init__(self, parent=None):
        super(EGLSyncGroup, self).__init__(parent=parent)
        self.ui = Ui_EGLSyncGroup()
        self.ui.setupUi(self)
        self.core = RareCore.instance().core()

        self.egl_path_info_label = QLabel(self.tr("Estimated path"), self)
        self.egl_path_info = ElideLabel("", parent=self)
        self.egl_path_info.setProperty("infoLabel", 1)
        self.ui.egl_sync_layout.insertRow(
            self.ui.egl_sync_layout.indexOf(self.ui.egl_path_edit_label) + 1,
            self.egl_path_info_label, self.egl_path_info
        )

        if platform.system() == "Windows":
            self.ui.egl_path_edit_label.setVisible(False)
            self.egl_path_info_label.setVisible(False)
            self.egl_path_info.setVisible(False)
        else:
            self.egl_path_edit = PathEdit(
                path=self.core.egl.programdata_path,
                placeholder=self.tr(
                    "Path to the Wine prefix where EGL is installed, or the Manifests folder"
                ),
                file_mode=QFileDialog.DirectoryOnly,
                edit_func=self.egl_path_edit_edit_cb,
                save_func=self.egl_path_edit_save_cb,
                parent=self,
            )
            self.egl_path_edit.textChanged.connect(self.egl_path_changed)
            self.ui.egl_path_edit_layout.addWidget(self.egl_path_edit)

            if not self.core.egl.programdata_path:
                self.egl_path_info.setText(self.tr("Updating..."))
                wine_resolver = WineResolver(
                    self.core, PathSpec.egl_programdata, "default"
                )
                wine_resolver.signals.result_ready.connect(self.wine_resolver_cb)
                QThreadPool.globalInstance().start(wine_resolver)
            else:
                self.egl_path_info_label.setVisible(False)
                self.egl_path_info.setVisible(False)

        self.ui.egl_sync_check.setChecked(self.core.egl_sync_enabled)
        self.ui.egl_sync_check.stateChanged.connect(self.egl_sync_changed)

        self.import_list = EGLSyncImportGroup(parent=self)
        self.ui.import_export_layout.addWidget(self.import_list)
        self.export_list = EGLSyncExportGroup(parent=self)
        self.ui.import_export_layout.addWidget(self.export_list)

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
    def egl_path_edit_edit_cb(path) -> Tuple[bool, str, int]:
        if not path:
            return True, path, IndicatorReasonsCommon.VALID
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
            return False, path, IndicatorReasonsCommon.WRONG_FORMAT
        if os.path.exists(path):
            return True, path, IndicatorReasonsCommon.VALID
        return False, path, IndicatorReasonsCommon.DIR_NOT_EXISTS

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
            self.ui.egl_sync_check.setEnabled(bool(path))
        self.ui.egl_sync_check.setCheckState(Qt.Unchecked)
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
            QThreadPool.globalInstance().start(sync_worker)
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
        self.ui.egl_sync_check_label.setEnabled(have_path)
        self.ui.egl_sync_check.setEnabled(have_path)
        self.import_list.populate(have_path)
        self.import_list.setEnabled(have_path)
        self.export_list.populate(have_path)
        self.export_list.setEnabled(have_path)
        # self.egl_watcher.blockSignals(False)


class EGLSyncListItem(QListWidgetItem):
    def __init__(self, game: Union[EGLManifest,InstalledGame], parent=None):
        super(EGLSyncListItem, self).__init__(parent=parent)
        self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        self.setCheckState(Qt.Unchecked)
        self.core = RareCore.instance().core()
        self.game = game
        self.setText(self.app_title)

    def is_checked(self) -> bool:
        return self.checkState() == Qt.Checked

    @abstractmethod
    def action(self) -> Union[str, bool]:
        pass

    @property
    def app_name(self):
        return self.game.app_name

    @property
    @abstractmethod
    def app_title(self) -> str:
        pass


class EGLSyncExportItem(EGLSyncListItem):
    def __init__(self, game: InstalledGame, parent=None):
        super(EGLSyncExportItem, self).__init__(game=game, parent=parent)

    def action(self) -> Union[str,bool]:
        error = False
        try:
            self.core.egl_export(self.game.app_name)
        except LgndrException as ret:
            error = ret.message
        return error

    @property
    def app_title(self) -> str:
        return self.game.title


class EGLSyncImportItem(EGLSyncListItem):
    def __init__(self, game: EGLManifest, parent=None):
        super(EGLSyncImportItem, self).__init__(game=game, parent=parent)

    def action(self) -> Union[str,bool]:
        error = False
        try:
            self.core.egl_import(self.game.app_name)
        except LgndrException as ret:
            error = ret.message
        return error

    @property
    def app_title(self) -> str:
        return self.core.get_game(self.game.app_name).app_title


class EGLSyncListGroup(QGroupBox):
    action_errors = pyqtSignal(list)

    def __init__(self, parent=None):
        super(EGLSyncListGroup, self).__init__(parent=parent)
        self.ui = Ui_EGLSyncListGroup()
        self.ui.setupUi(self)
        self.ui.list.setFrameShape(QFrame.NoFrame)
        self.rcore = RareCore.instance()
        self.core = RareCore.instance().core()

        self.ui.list.itemDoubleClicked.connect(
            lambda item: item.setCheckState(Qt.Unchecked)
            if item.checkState() != Qt.Unchecked
            else item.setCheckState(Qt.Checked)
        )
        self.ui.list.itemChanged.connect(self.has_selected)

        self.ui.select_all_button.clicked.connect(lambda: self.mark(Qt.Checked))
        self.ui.select_none_button.clicked.connect(lambda: self.mark(Qt.Unchecked))

        self.ui.action_button.clicked.connect(self.action)

        self.action_errors.connect(self.show_errors)

    def has_selected(self):
        for item in self.items:
            if item.is_checked():
                self.ui.action_button.setEnabled(True)
                return
        self.ui.action_button.setEnabled(False)

    def mark(self, state):
        for item in self.items:
            item.setCheckState(state)

    def populate(self, enabled: bool):
        self.ui.label.setVisible(not enabled or not bool(self.ui.list.count()))
        self.ui.list.setVisible(enabled and bool(self.ui.list.count()))
        self.ui.buttons_widget.setVisible(enabled and bool(self.ui.list.count()))

    @abstractmethod
    def action(self):
        pass

    @pyqtSlot(list)
    @abstractmethod
    def show_errors(self, errors: List):
        pass

    @property
    def items(self) -> Iterable[EGLSyncListItem]:
        # for i in range(self.list.count()):
        #     yield self.list.item(i)
        return [self.ui.list.item(i) for i in range(self.ui.list.count())]


class EGLSyncExportGroup(EGLSyncListGroup):
    def __init__(self, parent=None):
        super(EGLSyncExportGroup, self).__init__(parent=parent)
        self.setTitle(self.tr("Exportable games"))
        self.ui.label.setText(self.tr("No games to export to EGL"))
        self.ui.action_button.setText(self.tr("Export"))

    def populate(self, enabled: bool):
        if enabled:
            self.ui.list.clear()
            for item in self.core.egl_get_exportable():
                try:
                    i = EGLSyncExportItem(item, self.ui.list)
                except AttributeError:
                    logger.error(f"{item.app_name} does not work. Ignoring")
                else:
                    self.ui.list.addItem(i)
        super(EGLSyncExportGroup, self).populate(enabled)

    @pyqtSlot(list)
    def show_errors(self, errors: List):
        QMessageBox.warning(
            self.parent(),
            self.tr("The following errors occurred while exporting."),
            "\n".join(errors),
        )

    def action(self):
        errors: List = []
        for item in self.items:
            if item.is_checked():
                if e := item.action():
                    errors.append(e)
        self.populate(True)
        if errors:
            self.action_errors.emit(errors)


class EGLSyncImportGroup(EGLSyncListGroup):
    def __init__(self, parent=None):
        super(EGLSyncImportGroup, self).__init__(parent=parent)
        self.setTitle(self.tr("Importable games"))
        self.ui.label.setText(self.tr("No games to import from EGL"))
        self.ui.action_button.setText(self.tr("Import"))
        self.list_func = self.core.egl_get_importable

    def populate(self, enabled: bool):
        if enabled:
            self.ui.list.clear()
            for item in self.core.egl_get_importable():
                try:
                    i = EGLSyncImportItem(item, self.ui.list)
                except AttributeError:
                    logger.error(f"{item.app_name} does not work. Ignoring")
                else:
                    self.ui.list.addItem(i)
        super(EGLSyncImportGroup, self).populate(enabled)

    @pyqtSlot(list)
    def show_errors(self, errors: List):
        QMessageBox.warning(
            self.parent(),
            self.tr("The following errors occurred while importing."),
            "\n".join(errors),
        )

    def action(self):
        errors: List = []
        for item in self.items:
            if item.is_checked():
                if e := item.action():
                    errors.append(e)
                else:
                    self.rcore.get_game(item.app_name).set_installed(True)
        self.populate(True)
        if errors:
            self.action_errors.emit(errors)


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

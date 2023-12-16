import json
import os
from dataclasses import dataclass
from enum import IntEnum
from logging import getLogger
from pathlib import Path
from typing import List, Tuple, Optional, Set

from PyQt5.QtCore import Qt, QModelIndex, pyqtSignal, QRunnable, QObject, QThreadPool, pyqtSlot
from PyQt5.QtGui import QStandardItemModel, QShowEvent
from PyQt5.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QCompleter,
    QTreeView,
    QHeaderView,
    QMessageBox,
    QStackedWidget,
    QProgressBar,
    QSizePolicy,
    QFormLayout,
)

from rare.lgndr.cli import LegendaryCLI
from rare.lgndr.core import LegendaryCore
from rare.lgndr.glue.arguments import LgndrImportGameArgs
from rare.lgndr.glue.monkeys import LgndrIndirectStatus, get_boolean_choice_factory
from rare.shared import RareCore
from rare.ui.components.tabs.games.integrations.import_group import Ui_ImportGroup
from rare.widgets.elide_label import ElideLabel
from rare.widgets.indicator_edit import IndicatorLineEdit, IndicatorReasonsCommon, PathEdit

logger = getLogger("Import")


def find_app_name(path: str, core) -> Optional[str]:
    if os.path.exists(os.path.join(path, ".egstore")):
        for i in os.listdir(os.path.join(path, ".egstore")):
            if i.endswith(".mancpn"):
                with open(os.path.join(path, ".egstore", i)) as file:
                    app_name = json.load(file).get("AppName")
                return app_name
    elif app_name := LegendaryCLI(core).resolve_aliases(os.path.basename(os.path.normpath(path))):
        # return None if game does not exist (Workaround for overlay)
        if not core.get_game(app_name):
            return None
        return app_name
    else:
        logger.warning(f"Could not find AppName for {path}")
    return None


class ImportResult(IntEnum):
    ERROR = 0
    FAILED = 1
    SUCCESS = 2


@dataclass
class ImportedGame:
    result: ImportResult
    path: Optional[str] = None
    app_name: Optional[str] = None
    app_title: Optional[str] = None
    message: Optional[str] = None


class ImportWorker(QRunnable):
    class Signals(QObject):
        progress = pyqtSignal(ImportedGame, int)
        result = pyqtSignal(list)

    def __init__(
            self,
            core: LegendaryCore,
            path: str,
            app_name: str = None,
            platform: Optional[str] = None,
            import_folder: bool = False,
            import_dlcs: bool = False,
            import_force: bool = False
    ):
        super(ImportWorker, self).__init__()
        self.setAutoDelete(True)
        self.signals = ImportWorker.Signals()
        self.core = core

        self.path = Path(path)
        self.app_name = app_name
        self.import_folder = import_folder
        self.platform = platform if platform is not None else self.core.default_platform
        self.import_dlcs = import_dlcs
        self.import_force = import_force

    def run(self) -> None:
        result_list: List = []
        if self.import_folder:
            folders = [i for i in self.path.iterdir() if i.is_dir()]
            number_of_folders = len(folders)
            for i, child in enumerate(folders):
                if not child.is_dir():
                    continue
                result = self.__try_import(child, None)
                result_list.append(result)
                self.signals.progress.emit(result, int(100 * i // number_of_folders))
        else:
            result = self.__try_import(self.path, self.app_name)
            result_list.append(result)
            self.signals.progress.emit(result, 100)
        self.signals.result.emit(result_list)

    def __try_import(self, path: Path, app_name: str = None) -> ImportedGame:
        result = ImportedGame(ImportResult.ERROR)
        result.path = str(path)
        if app_name or (app_name := find_app_name(str(path), self.core)):
            game = self.core.get_game(app_name)
            result.app_name = app_name
            result.app_title = game.app_title
            platform = self.platform
            if platform not in self.core.get_game(app_name, update_meta=False).asset_infos:
                platform = "Windows"
            success, message = self.__import_game(path, app_name, platform)
            if not success:
                result.result = ImportResult.FAILED
                result.message = message
            else:
                result.result = ImportResult.SUCCESS
        return result

    def __import_game(self, path: Path, app_name: str, platform: str):
        cli = LegendaryCLI(self.core)
        status = LgndrIndirectStatus()
        args = LgndrImportGameArgs(
            app_path=str(path),
            app_name=app_name,
            platform=platform,
            disable_check=self.import_force,
            skip_dlcs=not self.import_dlcs,
            with_dlcs=self.import_dlcs,
            indirect_status=status,
            get_boolean_choice=get_boolean_choice_factory(self.import_dlcs)
        )
        cli.import_game(args)
        return status.success, status.message


class AppNameCompleter(QCompleter):
    activated = pyqtSignal(str)

    def __init__(self, app_names: Set[Tuple[str, str]], parent=None):
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
        self.rcore = RareCore.instance()
        self.core = RareCore.instance().core()

        self.worker: Optional[ImportWorker] = None
        self.threadpool = QThreadPool.globalInstance()

        self.__app_names: Set[str] = set()
        self.__install_dirs: Set[str] = set()

        self.path_edit = PathEdit(
            self.core.get_default_install_dir(self.core.default_platform),
            QFileDialog.DirectoryOnly,
            edit_func=self.path_edit_callback,
            parent=self,
        )
        self.path_edit.textChanged.connect(self.path_changed)
        self.ui.import_layout.setWidget(
            self.ui.import_layout.getWidgetPosition(self.ui.path_edit_label)[0],
            QFormLayout.FieldRole, self.path_edit
        )

        self.app_name_edit = IndicatorLineEdit(
            placeholder=self.tr("Use in case the app name was not found automatically"),
            edit_func=self.app_name_edit_callback,
            save_func=self.app_name_save_callback,
            parent=self,
        )
        self.app_name_edit.textChanged.connect(self.app_name_changed)
        self.ui.import_layout.setWidget(
            self.ui.import_layout.getWidgetPosition(self.ui.app_name_label)[0],
            QFormLayout.FieldRole, self.app_name_edit
        )

        self.ui.import_folder_check.stateChanged.connect(self.import_folder_changed)
        self.ui.import_dlcs_check.setEnabled(False)
        self.ui.import_dlcs_check.stateChanged.connect(self.import_dlcs_changed)

        self.ui.import_button_label.setText("")
        self.ui.import_button.setEnabled(False)
        self.ui.import_button.clicked.connect(
            lambda: self.__import(self.path_edit.text())
        )

        self.button_info_stack = QStackedWidget(self)
        self.button_info_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.button_info_stack.setFixedHeight(self.ui.import_button.sizeHint().height())
        self.info_label = ElideLabel(text="", parent=self.button_info_stack)
        self.info_label.setFixedHeight(False)
        self.info_label.setAlignment(Qt.AlignVCenter)
        self.info_progress = QProgressBar(self.button_info_stack)
        self.button_info_stack.addWidget(self.info_label)
        self.button_info_stack.addWidget(self.info_progress)
        self.ui.button_info_layout.insertWidget(0, self.button_info_stack)

    def showEvent(self, a0: QShowEvent) -> None:
        if a0.spontaneous():
            return super().showEvent(a0)
        self.__app_names = {rgame.app_name for rgame in self.rcore.games}
        self.__install_dirs = {rgame.folder_name for rgame in self.rcore.games if not rgame.is_dlc}
        self.app_name_edit.setCompleter(
            AppNameCompleter(app_names={(rgame.app_name, rgame.app_title) for rgame in self.rcore.games})
        )
        super().showEvent(a0)

    def set_game(self, app_name: str):
        if app_name:
            rgame = self.rcore.get_game(app_name)
            self.path_edit.setText(
                os.path.join(self.core.get_default_install_dir(rgame.default_platform), rgame.folder_name)
            )
            self.app_name_edit.setText(app_name)

    def path_edit_callback(self, path) -> Tuple[bool, str, int]:
        if os.path.exists(path):
            if os.path.exists(os.path.join(path, ".egstore")):
                return True, path, IndicatorReasonsCommon.VALID
            elif os.path.basename(path) in self.__install_dirs:
                return True, path, IndicatorReasonsCommon.VALID
        else:
            return False, path, IndicatorReasonsCommon.DIR_NOT_EXISTS
        return False, path, IndicatorReasonsCommon.UNDEFINED

    @pyqtSlot(str)
    def path_changed(self, path: str):
        self.info_label.setText("")
        self.ui.import_folder_check.setCheckState(Qt.Unchecked)
        self.ui.import_force_check.setCheckState(Qt.Unchecked)
        if self.path_edit.is_valid:
            self.app_name_edit.setText(find_app_name(path, self.core))
        else:
            self.app_name_edit.setText("")

    def app_name_edit_callback(self, text) -> Tuple[bool, str, int]:
        if not text:
            return False, text, IndicatorReasonsCommon.UNDEFINED
        if text in self.__app_names:
            return True, text, IndicatorReasonsCommon.VALID
        else:
            return False, text, IndicatorReasonsCommon.NOT_INSTALLED

    def app_name_save_callback(self, text) -> None:
        rgame = self.rcore.get_game(text)
        self.ui.platform_combo.clear()
        self.ui.platform_combo.addItems(rgame.platforms)
        self.ui.platform_combo.setCurrentText(rgame.default_platform)

    @pyqtSlot(str)
    def app_name_changed(self, app_name: str):
        self.info_label.setText("")
        self.ui.import_dlcs_check.setCheckState(Qt.Unchecked)
        self.ui.import_force_check.setCheckState(Qt.Unchecked)
        self.ui.import_dlcs_check.setEnabled(
            self.app_name_edit.is_valid and bool(self.core.get_dlc_for_game(app_name))
        )
        self.ui.import_button.setEnabled(
            not bool(self.worker) and (self.app_name_edit.is_valid and self.path_edit.is_valid)
        )

    @pyqtSlot(int)
    def import_folder_changed(self, state: Qt.CheckState):
        self.app_name_edit.setEnabled(not state)
        self.ui.platform_combo.setEnabled(not state)
        self.ui.platform_combo.setToolTip(
            self.tr(
                "When importing multiple games, the current OS will be used at the"
                " platform for the games that support it, otherwise the Windows version"
                " will be imported."
            ) if state else ""
        )
        self.ui.import_dlcs_check.setCheckState(Qt.Unchecked)
        self.ui.import_force_check.setCheckState(Qt.Unchecked)
        self.ui.import_dlcs_check.setEnabled(
            state
            or (self.app_name_edit.is_valid and bool(self.core.get_dlc_for_game(self.app_name_edit.text())))
        )
        self.ui.import_button.setEnabled(
            not bool(self.worker) and (state or (not state and self.app_name_edit.is_valid))
        )

    @pyqtSlot(int)
    def import_dlcs_changed(self, state: Qt.CheckState):
        self.ui.import_button.setEnabled(
            not bool(self.worker) and (self.ui.import_folder_check.isChecked() or self.app_name_edit.is_valid)
        )

    @pyqtSlot(str)
    def __import(self, path: Optional[str] = None):
        self.ui.import_button.setDisabled(True)
        self.info_label.setText(self.tr("Status: Importing games"))
        self.info_progress.setValue(0)
        self.button_info_stack.setCurrentWidget(self.info_progress)

        if not path:
            path = self.path_edit.text()
        self.worker = ImportWorker(
            self.core,
            path,
            app_name=self.app_name_edit.text(),
            platform=self.ui.platform_combo.currentText() if not self.ui.import_folder_check.isChecked() else None,
            import_folder=self.ui.import_folder_check.isChecked(),
            import_dlcs=self.ui.import_dlcs_check.isChecked(),
            import_force=self.ui.import_force_check.isChecked()
        )
        self.worker.signals.progress.connect(self.__on_import_progress)
        self.worker.signals.result.connect(self.__on_import_result)
        self.threadpool.start(self.worker)

    @pyqtSlot(ImportedGame, int)
    def __on_import_progress(self, imported: ImportedGame, progress: int):
        self.info_progress.setValue(progress)
        if imported.result == ImportResult.SUCCESS:
            self.rcore.get_game(imported.app_name).set_installed(True)
        status = "error" if not imported.result else (
            "failed" if imported.result == ImportResult.FAILED else "successful"
        )
        logger.info(f"Import {status}: {imported.app_title}: {imported.path} ({imported.message})")

    @pyqtSlot(list)
    def __on_import_result(self, result: List[ImportedGame]):
        self.worker = None
        self.button_info_stack.setCurrentWidget(self.info_label)
        if len(result) == 1:
            res = result[0]
            if res.result == ImportResult.SUCCESS:
                self.info_label.setText(
                    self.tr("Success: <b>{}</b> imported").format(res.app_title)
                )
            elif res.result == ImportResult.FAILED:
                self.info_label.setText(
                    self.tr("Failed: <b>{}</b> - {}").format(res.app_title, res.message)
                )
            else:
                self.info_label.setText(
                    self.tr("Error: Could not find AppName for <b>{}</b>").format(res.path)
                )
        else:
            self.info_label.setText(self.tr("Status: Finished importing games"))
            success = [r for r in result if r.result == ImportResult.SUCCESS]
            failure = [r for r in result if r.result == ImportResult.FAILED]
            errored = [r for r in result if r.result == ImportResult.ERROR]
            # pylint: disable=E1101
            messagebox = QMessageBox(
                QMessageBox.Information,
                self.tr("Import summary"),
                self.tr(
                    "Tried to import {} folders.\n\n"
                    "Successfully imported {} games, failed to import {} games and {} errors occurred"
                ).format(len(success) + len(failure) + len(errored), len(success), len(failure), len(errored)),
                buttons=QMessageBox.StandardButton.Close,
                parent=self,
            )
            messagebox.setWindowModality(Qt.NonModal)
            details: List = []
            for res in success:
                details.append(
                    self.tr("Success: {} imported").format(res.app_title)
                )
            for res in failure:
                details.append(
                    self.tr("Failed: {} - {}").format(res.app_title, res.message)
                )
            for res in errored:
                details.append(
                    self.tr("Error: Could not find AppName for {}").format(res.path)
                )
            messagebox.setDetailedText("\n".join(details))
            messagebox.show()

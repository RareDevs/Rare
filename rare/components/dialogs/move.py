import os
from pathlib import Path
from typing import Optional, Tuple, Union

from PySide6.QtCore import QThreadPool, Signal, Slot
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QFileDialog, QFormLayout, QLabel, QWidget

from rare.models.game import RareGame
from rare.models.install import MoveGameModel
from rare.shared import RareCore
from rare.shared.workers.move import MoveInfoWorker, MovePathEditReasons
from rare.ui.components.dialogs.move_dialog import Ui_MoveDialog
from rare.utils.misc import format_size, qta_icon
from rare.widgets.dialogs import ActionDialog, game_title
from rare.widgets.indicator_edit import IndicatorReasonsCommon, PathEdit


class MoveDialog(ActionDialog):
    result_ready = Signal(RareGame, MoveGameModel)

    def __init__(self, rcore: RareCore, rgame: RareGame, parent=None):
        super(MoveDialog, self).__init__(parent=parent)
        header = self.tr("Move")
        self.setWindowTitle(game_title(header, rgame.app_title))
        self.setSubtitle(game_title(header, rgame.app_title))

        self.threadpool = QThreadPool(self)
        self.threadpool.setMaxThreadCount(1)

        move_widget = QWidget(self)
        self.ui = Ui_MoveDialog()
        self.ui.setupUi(move_widget)

        self.rcore = rcore
        self.core = rcore.core()
        self.rgame: Optional[RareGame] = rgame
        self.options: MoveGameModel = MoveGameModel(rgame.app_name)
        self.options.target_path = os.path.dirname(rgame.install_path)
        self.options.target_name = os.path.basename(rgame.install_path)

        self.target_path_edit = PathEdit(
            path=self.options.target_path,
            file_mode=QFileDialog.FileMode.Directory,
            edit_func=self.__target_dir_edit_callback,
            parent=self,
        )
        self.target_path_edit.reasons = {
            MovePathEditReasons.MOVEDIALOG_DST_MISSING: self.tr("You need to provide the destination directory."),
            MovePathEditReasons.MOVEDIALOG_NO_WRITE: self.tr("No write permission on destination."),
            MovePathEditReasons.MOVEDIALOG_SAME_DIR: self.tr("Same directory or subdirectory selected."),
            MovePathEditReasons.MOVEDIALOG_DST_IN_SRC: self.tr("Destination is inside source directory"),
            MovePathEditReasons.MOVEDIALOG_NESTED_DIR: self.tr("Game install directories cannot be nested."),
            MovePathEditReasons.MOVEDIALOG_NO_SPACE: self.tr("Not enough space available on drive."),
        }
        self.target_path_edit.validationFinished.connect(self.__on_target_dir_validation)
        self.ui.main_layout.setWidget(
            self.ui.main_layout.getWidgetPosition(self.ui.target_path_label)[0],
            QFormLayout.ItemRole.FieldRole,
            self.target_path_edit,
        )

        self.accept_button.setText(self.tr("Move"))
        self.accept_button.setIcon(qta_icon("mdi.folder-move-outline"))
        self.accept_button.setObjectName("MoveButton")

        self.action_button.setText(self.tr("Validate"))
        self.action_button.setIcon(qta_icon("fa.check", "fa5s.check"))

        self.setCentralWidget(move_widget)

    def showEvent(self, a0: QShowEvent) -> None:
        if a0.spontaneous():
            return super().showEvent(a0)
        self.target_path_edit.refresh()
        return super().showEvent(a0)

    def action_handler(self):
        self.set_error_labels()
        message = self.tr("Updating...")
        self.set_size_labels(message, message)
        self.setActive(True, disable=False)
        self.options.target_path = self.target_path_edit.text()
        info_worker = MoveInfoWorker(self.rgame, self.rcore.installed_games, self.options)
        info_worker.signals.result.connect(self.__on_worker_result)
        self.threadpool.start(info_worker)

    def done_handler(self):
        self.threadpool.clear()
        self.threadpool.waitForDone()
        self.result_ready.emit(self.rgame, self.options)

    def accept_handler(self):
        self.options.accepted = True
        self.options.target_path = self.target_path_edit.text()

    def reject_handler(self):
        self.options.accepted = False
        self.options.target_path = ""

    @staticmethod
    def __target_dir_edit_callback(path: str) -> Tuple[bool, str, int]:
        if not path:
            return False, path, IndicatorReasonsCommon.IS_EMPTY
        try:
            perms_path = os.path.join(path, ".rare_perms")
            open(perms_path, "w").close()
            os.unlink(perms_path)
        except PermissionError:
            return False, path, IndicatorReasonsCommon.PERM_NO_WRITE
        except FileNotFoundError:
            return False, path, IndicatorReasonsCommon.DIR_NOT_EXISTS
        return True, path, IndicatorReasonsCommon.VALID

    @Slot(bool, object, object, MovePathEditReasons)
    def __on_worker_result(
        self, is_valid: bool, src_size: Union[int, float], dst_size: Union[int, float], reason: MovePathEditReasons
    ):
        self.setActive(False, disable=False)
        self.set_size_labels(src_size, dst_size)
        self.action_button.setEnabled(False)
        self.accept_button.setEnabled(is_valid)
        error, reason = (self.tr("Error"), self.target_path_edit.reasons[reason]) if not is_valid else ("", "")
        self.set_error_labels(error, reason)

    @Slot(bool, str)
    def __on_target_dir_validation(self, is_valid: bool, reason: str):
        path = Path(self.target_path_edit.text())
        self.ui.install_path_info.setText(str(path.joinpath(self.options.target_name)))
        self.action_button.setEnabled(is_valid and not self.active())
        self.accept_button.setEnabled(False)
        error, reason = (self.tr("Error"), reason) if not is_valid else ("", "")
        self.set_error_labels(error, reason)

    @staticmethod
    def __set_size_label(label: QLabel, value: Union[int, float, str]):
        is_numeric = isinstance(value, (int, float))
        font = label.font()
        font.setBold(is_numeric)
        font.setItalic(not is_numeric)
        label.setFont(font)
        text = format_size(value) if is_numeric else value
        label.setText(text)

    def set_size_labels(self, required: Union[int, float, str], available: Union[int, float, str]):
        self.__set_size_label(self.ui.required_space_text, required)
        self.__set_size_label(self.ui.available_space_text, available)

    def set_error_labels(self, label: str = "", message: str = ""):
        self.ui.warning_label.setVisible(bool(label))
        self.ui.warning_label.setText(label)
        self.ui.warning_text.setVisible(bool(message))
        self.ui.warning_text.setText(message)

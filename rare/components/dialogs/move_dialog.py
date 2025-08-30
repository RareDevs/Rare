import os
import shutil
from enum import auto
from typing import Tuple, Optional, Union

from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QFileDialog, QWidget, QFormLayout, QLabel

from rare.models.game import RareGame
from rare.models.install import MoveGameModel
from rare.shared import RareCore
from rare.ui.components.dialogs.move_dialog import Ui_MoveDialog
from rare.utils.misc import path_size, format_size, qta_icon
from rare.widgets.dialogs import ActionDialog, game_title
from rare.widgets.indicator_edit import PathEdit, IndicatorReasons, IndicatorReasonsCommon


class MovePathEditReasons(IndicatorReasons):
    MOVEDIALOG_DST_MISSING = auto()
    MOVEDIALOG_NO_WRITE = auto()
    MOVEDIALOG_SAME_DIR = auto()
    MOVEDIALOG_DST_IN_SRC = auto()
    MOVEDIALOG_NESTED_DIR = auto()
    MOVEDIALOG_NO_SPACE = auto()


class MoveDialog(ActionDialog):
    result_ready = Signal(RareGame, MoveGameModel)

    def __init__(self, rgame: RareGame, parent=None):
        super(MoveDialog, self).__init__(parent=parent)
        header = self.tr("Move")
        self.setWindowTitle(game_title(header, rgame.app_title))
        self.setSubtitle(game_title(header, rgame.app_title))

        move_widget = QWidget(self)
        self.ui = Ui_MoveDialog()
        self.ui.setupUi(move_widget)

        self.rcore = RareCore.instance()
        self.core = RareCore.instance().core()
        self.rgame: Optional[RareGame] = rgame
        self.options: MoveGameModel = MoveGameModel(rgame.app_name)

        self.target_dir_edit = PathEdit(
            path="", # path=rgame.install_path,
            file_mode=QFileDialog.FileMode.Directory,
            edit_func=self.__target_dir_edit_callback,
            parent=self
        )
        self.target_dir_edit.extend_reasons(
            {
                MovePathEditReasons.MOVEDIALOG_DST_MISSING: self.tr("You need to provide the destination directory."),
                MovePathEditReasons.MOVEDIALOG_NO_WRITE: self.tr("No write permission on destination."),
                MovePathEditReasons.MOVEDIALOG_SAME_DIR: self.tr("Same directory or subdirectory selected."),
                MovePathEditReasons.MOVEDIALOG_DST_IN_SRC: self.tr("Destination is inside source directory"),
                MovePathEditReasons.MOVEDIALOG_NESTED_DIR: self.tr("Game install directories cannot be nested."),
                MovePathEditReasons.MOVEDIALOG_NO_SPACE: self.tr("Not enough space available on drive."),
            }
        )
        self.target_dir_edit.validationFinished.connect(self.__on_target_dir_validation)
        self.ui.main_layout.setWidget(
            self.ui.main_layout.getWidgetPosition(self.ui.target_dir_label)[0],
            QFormLayout.ItemRole.FieldRole,
            self.target_dir_edit,
        )

        self.accept_button.setText(self.tr("Move"))
        self.accept_button.setIcon(qta_icon("mdi.folder-move-outline"))
        self.accept_button.setObjectName("MoveButton")

        self.action_button.setText(self.tr("Validate"))
        self.action_button.setIcon(qta_icon("fa.check", "fa5s.check"))
        self.action_button.setHidden(True)

        self.setCentralWidget(move_widget)

    def showEvent(self, a0: QShowEvent) -> None:
        if a0.spontaneous():
            return super().showEvent(a0)
        self.__update_widget()
        return super().showEvent(a0)

    def action_handler(self):
        pass

    def done_handler(self):
        self.result_ready.emit(self.rgame, self.options)

    def accept_handler(self):
        self.options.accepted = True
        self.options.target_path = self.target_dir_edit.text()

    def reject_handler(self):
        self.options.accepted = False
        self.options.target_path = ""

    @staticmethod
    def is_game_dir(src_path: str, dst_path: str):
        # This iterates over the destination dir, then iterates over the current install dir and if the file names
        # matches, we have an exisiting dir
        if os.path.isdir(dst_path):
            for dst_file in os.listdir(dst_path):
                for src_file in os.listdir(src_path):
                    if dst_file == src_file:
                        return True
        return False

    @staticmethod
    def __target_dir_edit_callback(path: str) -> Tuple[bool, str, int]:
        if not path:
            return False, path, IndicatorReasonsCommon.IS_EMPTY
        try:
            perms_path = os.path.join(path, ".rare_perms")
            open(perms_path, "w").close()
            os.unlink(perms_path)
        except PermissionError as e:
            return False, path, IndicatorReasonsCommon.PERM_NO_WRITE
        except FileNotFoundError as e:
            return False, path, IndicatorReasonsCommon.DIR_NOT_EXISTS
        return True, path, IndicatorReasonsCommon.VALID

    def __old_path_edit_callback_return(self, path, reason: int) -> Tuple[bool, str, int]:
        self.setActive(False)
        self.accept_button.setEnabled(False)
        return False, path, reason

    def __old_path_edit_callback(self, path: str) -> Tuple[bool, str, int]:
        self.setActive(True)
        self.set_size_labels("...", "...")

        if not self.rgame.install_path or not path:
            return self.__old_path_edit_callback_return(path, MovePathEditReasons.MOVEDIALOG_DST_MISSING)

        src_path = os.path.realpath(self.rgame.install_path)
        dst_path = os.path.realpath(path)
        dst_install_path = os.path.realpath(os.path.join(dst_path, os.path.basename(src_path)))

        if not os.path.isdir(dst_path):
            return self.__old_path_edit_callback_return(path, IndicatorReasonsCommon.DIR_NOT_EXISTS)

        # Get free space on drive and size of game folder
        _, _, free_space = shutil.disk_usage(dst_path)
        source_size = path_size(src_path)

        # Calculate from bytes to gigabytes
        self.set_size_labels(source_size, free_space)

        if not os.access(path, os.W_OK) or not os.access(self.rgame.install_path, os.W_OK):
            return self.__old_path_edit_callback_return(path, MovePathEditReasons.MOVEDIALOG_NO_WRITE)

        if src_path in {dst_path, dst_install_path}:
            return self.__old_path_edit_callback_return(path, MovePathEditReasons.MOVEDIALOG_SAME_DIR)

        if str(src_path) in str(dst_path):
            return self.__old_path_edit_callback_return(path, MovePathEditReasons.MOVEDIALOG_DST_IN_SRC)

        if str(dst_install_path) in str(src_path):
            return self.__old_path_edit_callback_return(path, MovePathEditReasons.MOVEDIALOG_DST_IN_SRC)

        for rgame in self.rcore.installed_games:
            if not rgame.is_non_asset and rgame.install_path in path:
                return self.__old_path_edit_callback_return(path, MovePathEditReasons.MOVEDIALOG_NESTED_DIR)

        is_existing_dir = self.is_game_dir(src_path, dst_install_path)

        for item in os.listdir(dst_path):
            if os.path.basename(src_path) in os.path.basename(item):
                if os.path.isdir(dst_install_path):
                    if not is_existing_dir:
                        self.ui.warning_text.setHidden(False)
                elif os.path.isfile(dst_install_path):
                    self.ui.warning_text.setHidden(False)

        if free_space <= source_size and not is_existing_dir:
            return self.__old_path_edit_callback_return(path, MovePathEditReasons.MOVEDIALOG_NO_SPACE)

        # Fallback
        self.setActive(False)
        self.accept_button.setEnabled(True)
        return True, path, IndicatorReasonsCommon.VALID

    def __on_target_dir_validation(self, is_valid: bool, reason: str):
        self.action_button.setEnabled(is_valid and not self.active())
        if is_valid:
            _is_valid, _path, _reason = self.__old_path_edit_callback(self.target_dir_edit.text())
            if not _is_valid:
                self.set_error_box(self.tr("Error"), self.target_dir_edit.reasons()[_reason])
            else:
                self.set_error_box()
            is_valid = _is_valid
        else:
            self.set_error_box(self.tr("Error"), reason)
        self.accept_button.setEnabled(is_valid)

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

    def set_error_box(self, label: str = "", message: str = ""):
        self.ui.warning_label.setVisible(bool(label))
        self.ui.warning_label.setText(label)
        self.ui.warning_text.setVisible(bool(message))
        self.ui.warning_text.setText(message)

    @Slot()
    def __update_widget(self):
        """React to state updates from RareGame"""
        if not self.rgame.is_installed or self.rgame.is_non_asset:
            self.setDisabled(True)
            return
        # FIXME: Make edit_func lighter instead of blocking signals
        # self.path_edit.line_edit.blockSignals(True)
        self.setActive(True)
        self.set_error_box(
            self.tr("Error"),
            self.tr("Moving here will overwrite <b>{}</b>").format(os.path.basename(self.rgame.install_path))
        )
        self.target_dir_edit.setText(self.rgame.install_path)
        # FIXME: Make edit_func lighter instead of blocking signals
        # self.path_edit.line_edit.blockSignals(False)
        self.setActive(False)

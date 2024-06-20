import os
import shutil
from enum import auto
from logging import getLogger
from typing import Tuple, Optional

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QLayout

from rare.models.install import MoveGameModel
from rare.models.game import RareGame
from rare.shared import RareCore
from rare.utils.misc import path_size, format_size, qta_icon
from rare.widgets.dialogs import ActionDialog, game_title
from rare.widgets.elide_label import ElideLabel
from rare.widgets.indicator_edit import PathEdit, IndicatorReasons, IndicatorReasonsCommon

logger = getLogger("MoveGame")


class MovePathEditReasons(IndicatorReasons):
    MOVEDIALOG_DST_MISSING = auto()
    MOVEDIALOG_NO_WRITE_PERM = auto()
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

        self.rcore = RareCore.instance()
        self.core = RareCore.instance().core()
        self.rgame: Optional[RareGame] = None

        self.path_edit = PathEdit("", QFileDialog.FileMode.Directory, edit_func=self.path_edit_callback)
        self.path_edit.extend_reasons({
            MovePathEditReasons.MOVEDIALOG_DST_MISSING: self.tr("You need to provide the destination directory."),
            MovePathEditReasons.MOVEDIALOG_NO_WRITE_PERM: self.tr("No write permission on destination."),
            MovePathEditReasons.MOVEDIALOG_SAME_DIR: self.tr("Same directory or subdirectory selected."),
            MovePathEditReasons.MOVEDIALOG_DST_IN_SRC: self.tr("Destination is inside source directory"),
            MovePathEditReasons.MOVEDIALOG_NESTED_DIR: self.tr("Game install directories cannot be nested."),
            MovePathEditReasons.MOVEDIALOG_NO_SPACE: self.tr("Not enough space available on drive."),
        })

        self.warn_label = ElideLabel("", parent=self)

        font = self.font()
        font.setBold(True)
        self.req_space_label = QLabel(self.tr("Required:"), self)
        self.req_space = QLabel(self)
        self.req_space.setFont(font)
        self.avail_space_label = QLabel(self.tr("Available:"), self)
        self.avail_space = QLabel(self)
        self.avail_space.setFont(font)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.req_space_label)
        bottom_layout.addWidget(self.req_space, stretch=1)
        bottom_layout.addWidget(self.avail_space_label)
        bottom_layout.addWidget(self.avail_space, stretch=1)

        layout = QVBoxLayout()
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        layout.addWidget(self.path_edit)
        layout.addWidget(self.warn_label)
        layout.addLayout(bottom_layout)

        self.setCentralLayout(layout)

        self.accept_button.setText(self.tr("Move"))
        self.accept_button.setIcon(qta_icon("mdi.folder-move-outline"))

        self.action_button.setHidden(True)

        self.update_game(rgame)

        self.options: MoveGameModel = MoveGameModel(rgame.app_name)

    def action_handler(self):
        pass

    def done_handler(self):
        self.result_ready.emit(self.rgame, self.options)

    def accept_handler(self):
        self.options.accepted = True
        self.options.target_path = self.path_edit.text()

    def reject_handler(self):
        self.options.accepted = False
        self.options.target_path = ""

    def refresh_indicator(self):
        # needed so the edit_func gets run again
        text = self.path_edit.text()
        self.path_edit.setText(str())
        self.path_edit.setText(text)

    def path_edit_callback(self, path: str) -> Tuple[bool, str, int]:
        self.setActive(True)
        self.req_space.setText("...")
        self.avail_space.setText("...")

        def helper_func(reason: int) -> Tuple[bool, str, int]:
            self.setActive(False)
            self.accept_button.setEnabled(False)
            return False, path, reason

        if not self.rgame.install_path or not path:
            return helper_func(MovePathEditReasons.MOVEDIALOG_DST_MISSING)

        src_path = os.path.realpath(self.rgame.install_path)
        dst_path = os.path.realpath(path)
        dst_install_path = os.path.realpath(os.path.join(dst_path, os.path.basename(src_path)))

        if not os.path.isdir(dst_path):
            return helper_func(IndicatorReasonsCommon.DIR_NOT_EXISTS)

        # Get free space on drive and size of game folder
        _, _, free_space = shutil.disk_usage(dst_path)
        source_size = path_size(src_path)

        # Calculate from bytes to gigabytes
        self.req_space.setText(format_size(source_size))
        self.avail_space.setText(format_size(free_space))

        if not os.access(path, os.W_OK) or not os.access(self.rgame.install_path, os.W_OK):
            return helper_func(MovePathEditReasons.MOVEDIALOG_NO_WRITE_PERM)

        if src_path in {dst_path, dst_install_path}:
            return helper_func(MovePathEditReasons.MOVEDIALOG_SAME_DIR)

        if str(src_path) in str(dst_path):
            return helper_func(MovePathEditReasons.MOVEDIALOG_DST_IN_SRC)

        if str(dst_install_path) in str(src_path):
            return helper_func(MovePathEditReasons.MOVEDIALOG_DST_IN_SRC)

        for rgame in self.rcore.installed_games:
            if not rgame.is_non_asset and rgame.install_path in path:
                return helper_func(MovePathEditReasons.MOVEDIALOG_NESTED_DIR)

        is_existing_dir = is_game_dir(src_path, dst_install_path)

        for item in os.listdir(dst_path):
            if os.path.basename(src_path) in os.path.basename(item):
                if os.path.isdir(dst_install_path):
                    if not is_existing_dir:
                        self.warn_label.setHidden(False)
                elif os.path.isfile(dst_install_path):
                    self.warn_label.setHidden(False)

        if free_space <= source_size and not is_existing_dir:
            return helper_func(MovePathEditReasons.MOVEDIALOG_NO_SPACE)

        # Fallback
        self.setActive(False)
        self.accept_button.setEnabled(True)
        return True, path, IndicatorReasonsCommon.VALID

    @Slot()
    def __update_widget(self):
        """ React to state updates from RareGame """
        if not self.rgame.is_installed or self.rgame.is_non_asset:
            self.setDisabled(True)
            return
        # FIXME: Make edit_func lighter instead of blocking signals
        # self.path_edit.line_edit.blockSignals(True)
        self.setActive(True)
        self.warn_label.setText(
            self.warn_label.tr("Moving here will overwrite <b>{}</b>").format(os.path.basename(self.rgame.install_path))
        )
        self.warn_label.setHidden(False)
        self.path_edit.setText(self.rgame.install_path)
        # FIXME: Make edit_func lighter instead of blocking signals
        # self.path_edit.line_edit.blockSignals(False)
        self.setActive(False)
        # self.refresh_indicator()

    def update_game(self, rgame: RareGame):
        self.rgame = rgame
        self.__update_widget()


def is_game_dir(src_path: str, dst_path: str):
    # This iterates over the destination dir, then iterates over the current install dir and if the file names
    # matches, we have an exisiting dir
    if os.path.isdir(dst_path):
        for dst_file in os.listdir(dst_path):
            for src_file in os.listdir(src_path):
                if dst_file == src_file:
                    return True
    return False

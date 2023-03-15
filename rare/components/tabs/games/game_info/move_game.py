import os
import shutil
from enum import auto
from logging import getLogger
from typing import Tuple, Optional

from PyQt5.QtCore import pyqtSignal, Qt, pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog

from rare.models.game import RareGame
from rare.shared import RareCore
from rare.utils.misc import path_size, format_size
from rare.widgets.elide_label import ElideLabel
from rare.widgets.indicator_edit import PathEdit, IndicatorReasons, IndicatorReasonsCommon

logger = getLogger("MoveGame")


class MovePathEditReasons(IndicatorReasons):
    DST_MISSING = auto()
    NO_WRITE_PERM = auto()
    SAME_DIR = auto()
    DST_IN_SRC = auto()
    NESTED_DIR = auto()
    NO_SPACE = auto()


class MoveGamePopUp(QWidget):
    move_clicked = pyqtSignal(str)
    browse_done = pyqtSignal()

    def __init__(self, parent=None):
        super(MoveGamePopUp, self).__init__(parent=parent)
        self.rcore = RareCore.instance()
        self.core = RareCore.instance().core()
        self.rgame: Optional[RareGame] = None

        self.path_edit = PathEdit("", QFileDialog.Directory, edit_func=self.path_edit_callback)
        self.path_edit.extend_reasons({
            MovePathEditReasons.DST_MISSING: self.tr("You need to provide the destination directory."),
            MovePathEditReasons.NO_WRITE_PERM: self.tr("No write permission on destination."),
            MovePathEditReasons.SAME_DIR: self.tr("Same directory or subdirectory selected."),
            MovePathEditReasons.DST_IN_SRC: self.tr("Destination is inside source directory"),
            MovePathEditReasons.NESTED_DIR: self.tr("Game install directories cannot be nested."),
            MovePathEditReasons.NO_SPACE: self.tr("Not enough space available on drive."),
        })
        self.path_edit.path_select.clicked.connect(self.browse_done)

        self.button = QPushButton(self.tr("Move"))
        self.button.setFixedSize(self.path_edit.path_select.sizeHint())
        self.button.clicked.connect(lambda p: self.move_clicked.emit(self.path_edit.text()))

        self.warn_label = ElideLabel("", parent=self)

        middle_layout = QHBoxLayout()
        middle_layout.setAlignment(Qt.AlignRight)
        middle_layout.addWidget(self.warn_label, stretch=1)
        middle_layout.addWidget(self.button)

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

        layout: QVBoxLayout = QVBoxLayout(self)
        layout.addWidget(self.path_edit)
        layout.addLayout(middle_layout)
        layout.addLayout(bottom_layout)

    def refresh_indicator(self):
        # needed so the edit_func gets run again
        text = self.path_edit.text()
        self.path_edit.setText(str())
        self.path_edit.setText(text)

    def path_edit_callback(self, path: str) -> Tuple[bool, str, int]:
        self.button.setEnabled(True)
        self.warn_label.setHidden(False)
        self.req_space.setText("...")
        self.avail_space.setText("...")

        def helper_func(reason: int) -> Tuple[bool, str, int]:
            self.button.setEnabled(False)
            return False, path, reason

        if not self.rgame.install_path or not path:
            return helper_func(MovePathEditReasons.DST_MISSING)

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
            return helper_func(MovePathEditReasons.NO_WRITE_PERM)

        if src_path == dst_path or src_path == dst_install_path:
            return helper_func(MovePathEditReasons.SAME_DIR)

        if str(src_path) in str(dst_path):
            return helper_func(MovePathEditReasons.DST_IN_SRC)

        if str(dst_install_path) in str(src_path):
            return helper_func(MovePathEditReasons.DST_IN_SRC)

        for rgame in self.rcore.installed_games:
            if not rgame.is_non_asset and rgame.install_path in path:
                return helper_func(MovePathEditReasons.NESTED_DIR)

        is_existing_dir = is_game_dir(src_path, dst_install_path)

        for item in os.listdir(dst_path):
            if os.path.basename(src_path) in os.path.basename(item):
                if os.path.isdir(dst_install_path):
                    if not is_existing_dir:
                        self.warn_label.setHidden(False)
                elif os.path.isfile(dst_install_path):
                    self.warn_label.setHidden(False)

        if free_space <= source_size and not is_existing_dir:
            return helper_func(MovePathEditReasons.NO_SPACE)

        # Fallback
        self.button.setEnabled(True)
        return True, path, IndicatorReasonsCommon.VALID

    @pyqtSlot()
    def __update_widget(self):
        """ React to state updates from RareGame """
        if not self.rgame.is_installed or self.rgame.is_non_asset:
            self.setDisabled(True)
            return
        # FIXME: Make edit_func lighter instead of blocking signals
        self.path_edit.line_edit.blockSignals(True)
        self.path_edit.setText(self.rgame.install_path)
        # FIXME: Make edit_func lighter instead of blocking signals
        self.path_edit.line_edit.blockSignals(False)
        self.warn_label.setText(
            self.tr("Moving here will overwrite <b>{}</b>").format(os.path.basename(self.rgame.install_path))
        )
        self.refresh_indicator()

    def update_game(self, rgame: RareGame):
        if self.rgame is not None:
            self.rgame.signals.widget.update.disconnect(self.__update_widget)
        self.rgame = None
        rgame.signals.widget.update.connect(self.__update_widget)
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

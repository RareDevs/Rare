import os
import shutil
from logging import getLogger
from typing import Tuple, Optional

from PyQt5.QtCore import pyqtSignal, Qt, pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog

from rare.models.game import RareGame
from rare.shared import LegendaryCoreSingleton
from rare.utils.extra_widgets import PathEdit
from rare.widgets.elide_label import ElideLabel

logger = getLogger("MoveGame")


class MoveGamePopUp(QWidget):
    move_clicked = pyqtSignal(str)
    browse_done = pyqtSignal()

    def __init__(self, parent=None):
        super(MoveGamePopUp, self).__init__(parent=parent)
        self.core = LegendaryCoreSingleton()
        self.rgame: Optional[RareGame] = None

        self.path_edit = PathEdit("", QFileDialog.Directory, edit_func=self.path_edit_cb)
        self.path_edit.path_select.clicked.connect(self.browse_done)

        self.button = QPushButton(self.tr("Move"))
        self.button.setFixedSize(self.path_edit.path_select.sizeHint())
        self.button.clicked.connect(lambda p: self.move_clicked.emit(self.path_edit.text()))

        self.warn_label = ElideLabel("", parent=self)

        middle_layout = QHBoxLayout()
        middle_layout.setAlignment(Qt.AlignRight)
        middle_layout.addWidget(self.warn_label, stretch=1)
        middle_layout.addWidget(self.button)

        bottom_layout = QVBoxLayout()
        self.aval_space_label = QLabel(self)
        self.req_space_label = QLabel(self)
        bottom_layout.addWidget(self.aval_space_label)
        bottom_layout.addWidget(self.req_space_label)

        layout: QVBoxLayout = QVBoxLayout(self)
        layout.addWidget(self.path_edit)
        layout.addLayout(middle_layout)
        layout.addLayout(bottom_layout)

    def refresh_indicator(self):
        # needed so the edit_func gets run again
        text = self.path_edit.text()
        self.path_edit.setText(str())
        self.path_edit.setText(text)

    def path_edit_cb(self, path: str):
        self.button.setEnabled(True)
        self.warn_label.setHidden(False)

        def helper_func(reason: str) -> Tuple[bool, str, str]:
            self.button.setEnabled(False)
            return False, path, self.tr(reason)

        if not self.rgame.igame.install_path or not path:
            return helper_func("You need to provide a directory.")

        src_path = os.path.realpath(self.rgame.igame.install_path)
        dst_path = os.path.realpath(path)
        dst_install_path = os.path.realpath(os.path.join(dst_path, os.path.basename(src_path)))

        if not os.path.isdir(dst_path):
            return helper_func("Directory doesn't exist or file selected.")

        # Get free space on drive and size of game folder
        _, _, free_space = shutil.disk_usage(dst_path)
        source_size = sum(
            os.stat(os.path.join(dp, f)).st_size
            for dp, dn, filenames in os.walk(src_path)
            for f in filenames
        )

        # Calculate from bytes to gigabytes
        free_space = round(free_space / 1000 ** 3, 2)
        source_size = round(source_size / 1000 ** 3, 2)
        self.aval_space_label.setText(self.tr("Available space: {}GB".format(free_space)))
        self.req_space_label.setText(self.tr("Required space: {}GB").format(source_size))

        if not os.access(path, os.W_OK) or not os.access(self.rgame.igame.install_path, os.W_OK):
            return helper_func("No write permission on destination path/current install path.")

        if src_path == dst_path or src_path == dst_install_path:
            return helper_func("Same directory or parent directory selected.")

        if str(src_path) in str(dst_path):
            return helper_func("You can't select a directory that is inside the current install path.")

        if str(dst_install_path) in str(src_path):
            return helper_func("You can't select a directory which contains the game installation.")

        for game in self.core.get_installed_list():
            if game.install_path in path:
                return helper_func("Game installations cannot be nested due to unintended sideeffects.")

        is_existing_dir = is_game_dir(src_path, dst_install_path)

        for item in os.listdir(dst_path):
            if os.path.basename(src_path) in os.path.basename(item):
                if os.path.isdir(dst_install_path):
                    if not is_existing_dir:
                        self.warn_label.setHidden(False)
                elif os.path.isfile(dst_install_path):
                    self.warn_label.setHidden(False)

        if free_space <= source_size and not is_existing_dir:
            return helper_func("Not enough space available on drive.")

        # Fallback
        self.button.setEnabled(True)
        return True, path, str()

    @pyqtSlot()
    def __update_widget(self):
        """ React to state updates from RareGame """
        if not self.rgame.is_installed and not self.rgame.is_non_asset:
            self.setDisabled(True)
            return
        # FIXME: Make edit_func lighter instead of blocking signals
        self.path_edit.line_edit.blockSignals(True)
        self.path_edit.setText(self.rgame.igame.install_path)
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

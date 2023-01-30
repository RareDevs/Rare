import os
import shutil
from logging import getLogger
from pathlib import Path
from typing import Tuple

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog

from rare.shared import LegendaryCoreSingleton
from rare.utils.extra_widgets import PathEdit

logger = getLogger("MoveGame")


class MoveGamePopUp(QWidget):
    move_clicked = pyqtSignal(str)
    browse_done = pyqtSignal()

    def __init__(self, parent=None):
        super(MoveGamePopUp, self).__init__(parent=parent)
        self.core = LegendaryCoreSingleton()
        self.install_path = ""
        self.move_path_edit = PathEdit("", QFileDialog.Directory, edit_func=self.edit_func_move_game)
        self.move_path_edit.path_select.clicked.connect(self.emit_browse_done_signal)

        self.move_button = QPushButton(self.tr("Move"))
        self.move_button.setFixedSize(self.move_path_edit.path_select.sizeHint())
        self.move_button.clicked.connect(self.emit_move_game_signal)

        self.warn_overwriting = QLabel()

        middle_layout = QHBoxLayout()
        middle_layout.setAlignment(Qt.AlignRight)
        middle_layout.addWidget(self.warn_overwriting, stretch=1)
        middle_layout.addWidget(self.move_button)

        bottom_layout = QVBoxLayout()
        self.aval_space_label = QLabel()
        self.req_space_label = QLabel()
        bottom_layout.addWidget(self.aval_space_label)
        bottom_layout.addWidget(self.req_space_label)

        layout: QVBoxLayout = QVBoxLayout()
        layout.addWidget(self.move_path_edit)
        layout.addLayout(middle_layout)
        layout.addLayout(bottom_layout)

        self.setLayout(layout)

    def emit_move_game_signal(self):
        self.move_clicked.emit(self.move_path_edit.text())

    def emit_browse_done_signal(self):
        self.browse_done.emit()

    def refresh_indicator(self):
        # needed so the edit_func gets run again
        text = self.move_path_edit.text()
        self.move_path_edit.setText(str())
        self.move_path_edit.setText(text)

    @staticmethod
    def is_different_drive(dir1: str, dir2: str):
        return os.stat(dir1).st_dev != os.stat(dir2).st_dev

    def edit_func_move_game(self, dir_selected):
        self.move_button.setEnabled(True)
        self.warn_overwriting.setHidden(True)

        def helper_func(reason: str) -> Tuple[bool, str, str]:
            self.move_button.setEnabled(False)
            return False, dir_selected, self.tr(reason)

        if not self.install_path or not dir_selected:
            return helper_func("You need to provide a directory.")

        install_path = Path(self.install_path).resolve()
        dest_path = Path(dir_selected).resolve()
        dest_path_with_suffix = dest_path.joinpath(install_path.stem).resolve()

        if not dest_path.is_dir():
            return helper_func("Directory doesn't exist or file selected.")

        # Get free space on drive and size of game folder
        _, _, free_space = shutil.disk_usage(dest_path)
        source_size = sum(f.stat().st_size for f in install_path.glob("**/*") if f.is_file())

        # Calculate from bytes to gigabytes
        free_space_dest_drive = round(free_space / 1000 ** 3, 2)
        source_size = round(source_size / 1000 ** 3, 2)
        self.aval_space_label.setText(self.tr("Available space: {}GB".format(free_space_dest_drive)))
        self.req_space_label.setText(self.tr("Required space: {}GB").format(source_size))

        if not os.access(dir_selected, os.W_OK) or not os.access(self.install_path, os.W_OK):
            return helper_func("No write permission on destination path/current install path.")

        if install_path == dest_path or install_path == dest_path_with_suffix:
            return helper_func("Same directory or parent directory selected.")

        if str(install_path) in str(dest_path):
            return helper_func("You can't select a directory that is inside the current install path.")

        if str(dest_path_with_suffix) in str(install_path):
            return helper_func("You can't select a directory which contains the game installation.")

        for game in self.core.get_installed_list():
            if game.install_path in dir_selected:
                return helper_func("Game installations cannot be nested due to unintended sideeffects.")

        is_existing_dir = is_game_dir(install_path, dest_path_with_suffix)

        for i in dest_path.iterdir():
            if install_path.stem in i.stem:
                if dest_path_with_suffix.is_dir():
                    if not is_existing_dir:
                        self.warn_overwriting.setHidden(False)
                elif dest_path_with_suffix.is_file():
                    self.warn_overwriting.setHidden(False)

        if free_space_dest_drive <= source_size and not is_existing_dir:
            return helper_func("Not enough space available on drive.")

        # Fallback
        self.move_button.setEnabled(True)
        return True, dir_selected, str()

    def update_game(self, app_name):
        igame = self.core.get_installed_game(app_name, skip_sync=True)
        if igame is None:
            return
        self.install_path = igame.install_path
        # FIXME: Make edit_func lighter instead of blocking signals
        self.move_path_edit.line_edit.blockSignals(True)
        self.move_path_edit.setText(igame.install_path)
        # FIXME: Make edit_func lighter instead of blocking signals
        self.move_path_edit.line_edit.blockSignals(False)
        self.warn_overwriting.setText(
            self.tr("Moving here will overwrite the dir/file {}/").format(Path(self.install_path).stem)
        )


def is_game_dir(install_path: Path, dest_path: Path):
    # This iterates over the destination dir, then iterates over the current install dir and if the file names
    # matches, we have an exisiting dir
    if dest_path.is_dir():
        for file in dest_path.iterdir():
            for install_file in install_path.iterdir():
                if file.name == install_file.name:
                    return True
    return False

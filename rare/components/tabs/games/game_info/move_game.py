import os
import shutil
from logging import getLogger
from pathlib import Path
from typing import Tuple

from PyQt5.QtCore import pyqtSignal, QRunnable, QObject, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog
from legendary.models.game import VerifyResult, InstalledGame
from legendary.utils.lfs import validate_files

from rare.shared import LegendaryCoreSingleton
from rare.utils.extra_widgets import PathEdit

logger = getLogger("MoveGame")


class MoveGamePopUp(QWidget):
    move_clicked = pyqtSignal(str)
    browse_done = pyqtSignal()

    def __init__(self):
        super(MoveGamePopUp, self).__init__()
        layout: QVBoxLayout = QVBoxLayout()
        self.install_path = str()
        self.core = LegendaryCoreSingleton()
        self.move_path_edit = PathEdit(str(), QFileDialog.Directory, edit_func=self.edit_func_move_game)
        self.move_path_edit.path_select.clicked.connect(self.emit_browse_done_signal)

        self.move_game = QPushButton(self.tr("Move"))
        self.move_game.setMaximumWidth(50)
        self.move_game.clicked.connect(self.emit_move_game_signal)

        self.warn_overwriting = QLabel()

        middle_layout = QHBoxLayout()
        middle_layout.setAlignment(Qt.AlignRight)
        middle_layout.addWidget(self.warn_overwriting, stretch=1)
        middle_layout.addWidget(self.move_game)

        bottom_layout = QVBoxLayout()
        self.aval_space_label = QLabel()
        self.req_space_label = QLabel()
        bottom_layout.addWidget(self.aval_space_label)
        bottom_layout.addWidget(self.req_space_label)

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

    # Thanks to lk.
    @staticmethod
    def find_mount(path):
        mount_point = path
        while path != path.anchor:
            if path.is_mount():
                return path
            else:
                path = path.parent
        return mount_point

    def edit_func_move_game(self, dir_selected):
        self.move_game.setEnabled(True)
        self.warn_overwriting.setHidden(True)

        def helper_func(reason: str) -> Tuple[bool, str, str]:
            self.move_game.setEnabled(False)
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
        self.move_game.setEnabled(True)
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


class CopyGameInstallation(QRunnable):
    class Signals(QObject):
        progress = pyqtSignal(int)
        finished = pyqtSignal(str)
        no_space_left = pyqtSignal()

    def __init__(
            self,
            install_path: str,
            dest_path: Path,
            is_existing_dir: bool,
            igame: InstalledGame,
    ):
        super(CopyGameInstallation, self).__init__()
        self.signals = CopyGameInstallation.Signals()
        self.install_path = install_path
        self.dest_path = dest_path
        self.source_size = 0
        self.dest_size = 0
        self.is_existing_dir = is_existing_dir
        self.core = LegendaryCoreSingleton()
        self.igame = igame
        self.file_list = None
        self.total: int = 0

    def run(self):
        root_directory = Path(self.install_path)
        self.source_size = sum(f.stat().st_size for f in root_directory.glob("**/*") if f.is_file())

        # if game dir is not existing, just copying:
        if not self.is_existing_dir:
            shutil.copytree(
                self.install_path,
                self.dest_path,
                copy_function=self.copy_each_file_with_progress,
                dirs_exist_ok=True,
            )
        else:
            manifest_data, _ = self.core.get_installed_manifest(self.igame.app_name)
            manifest = self.core.load_manifest(manifest_data)
            files = sorted(
                manifest.file_manifest_list.elements,
                key=lambda a: a.filename.lower(),
            )
            self.file_list = [(f.filename, f.sha_hash.hex()) for f in files]
            self.total = len(self.file_list)

            # recreate dir structure
            shutil.copytree(
                self.install_path,
                self.dest_path,
                copy_function=self.copy_dir_structure,
                dirs_exist_ok=True,
            )

            for i, (result, relative_path, _, _) in enumerate(
                    validate_files(str(self.dest_path), self.file_list)
            ):
                dst_path = f"{self.dest_path}/{relative_path}"
                src_path = f"{self.install_path}/{relative_path}"
                if Path(src_path).is_file():
                    if result == VerifyResult.HASH_MISMATCH:
                        try:
                            shutil.copy(src_path, dst_path)
                        except IOError:
                            self.signals.no_space_left.emit()
                            return
                    elif result == VerifyResult.FILE_MISSING:
                        try:
                            shutil.copy(src_path, dst_path)
                        except (IOError, OSError):
                            self.signals.no_space_left.emit()
                            return
                    elif result == VerifyResult.OTHER_ERROR:
                        logger.warning(f"Copying file {src_path} to {dst_path} failed")
                    self.signals.progress.emit(int(i * 10 / self.total * 10))
                else:
                    logger.warning(
                        f"Source dir does not have file {src_path}. File will be missing in the destination "
                        f"dir. "
                    )

        shutil.rmtree(self.install_path)
        self.signals.finished.emit(str(self.dest_path))

    def copy_each_file_with_progress(self, src, dst):
        shutil.copy(src, dst)
        self.dest_size += Path(src).stat().st_size
        self.signals.progress.emit(int(self.dest_size * 10 / self.source_size * 10))

    # This method is a copy_func, and only copies the src if it's a dir.
    # Thus, it can be used to re-create the dir strucute.
    @staticmethod
    def copy_dir_structure(src, dst):
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))
        if os.path.isdir(src):
            shutil.copyfile(src, dst)
            shutil.copystat(src, dst)
        return dst


def is_game_dir(install_path: Path, dest_path: Path):
    # This iterates over the destination dir, then iterates over the current install dir and if the file names
    # matches, we have an exisiting dir
    if dest_path.is_dir():
        for file in dest_path.iterdir():
            for install_file in install_path.iterdir():
                if file.name == install_file.name:
                    return True
    return False

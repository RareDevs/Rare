import os
import platform
import shutil
from pathlib import Path
from logging import getLogger
from typing import Tuple

from PyQt5.QtCore import (
    QObject,
    QRunnable,
    Qt,
    pyqtSignal,
    QThreadPool,
    pyqtSlot,
)
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QWidgetAction,
)

from legendary.models.game import Game, InstalledGame, VerifyResult
from rare.legendary.legendary.utils.lfs import validate_files
from rare.shared import (
    LegendaryCoreSingleton,
    GlobalSignalsSingleton,
    ArgumentsSingleton,
)
from rare.ui.components.tabs.games.game_info.game_info import Ui_GameInfo
from rare.utils.extra_widgets import PathEdit
from rare.utils.legendary_utils import VerifyWorker
from rare.utils.models import InstallOptionsModel
from rare.utils.steam_grades import SteamWorker
from rare.utils.utils import get_size, get_pixmap

logger = getLogger("GameInfo")


class GameInfo(QWidget, Ui_GameInfo):
    igame: InstalledGame
    game: Game = None
    verify_threads = dict()
    verification_finished = pyqtSignal(InstalledGame)
    uninstalled = pyqtSignal(str)

    def __init__(self, parent, game_utils):
        super(GameInfo, self).__init__(parent=parent)
        self.setupUi(self)
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()
        self.args = ArgumentsSingleton()
        self.game_utils = game_utils

        if platform.system() == "Windows":
            self.lbl_grade.setVisible(False)
            self.grade.setVisible(False)
        else:
            self.steam_worker = SteamWorker(self.core)
            self.steam_worker.signals.rating_signal.connect(self.grade.setText)
            self.steam_worker.setAutoDelete(False)

        self.game_actions_stack.setCurrentIndex(0)
        self.install_button.setText(self.tr("Link to Origin/Launch"))
        self.game_actions_stack.resize(self.game_actions_stack.minimumSize())

        self.uninstall_button.clicked.connect(self.uninstall)
        self.verify_button.clicked.connect(self.verify)

        self.verify_pool = QThreadPool()
        self.verify_pool.setMaxThreadCount(2)
        if self.args.offline:
            self.repair_button.setDisabled(True)
        else:
            self.repair_button.clicked.connect(self.repair)

        self.install_button.clicked.connect(lambda: self.game_utils.launch_game(self.game.app_name))

        self.move_game_pop_up = MoveGamePopUp()
        self.move_action = QWidgetAction(self)
        self.move_action.setDefaultWidget(self.move_game_pop_up)
        self.move_button.setMenu(QMenu())
        self.move_button.menu().addAction(self.move_action)

        self.progress_of_moving = QProgressBar()
        self.existing_game_dir = False
        self.is_moving = False
        self.game_moving = None
        self.dest_path_with_suffix = None

        self.widget_container = QWidget()
        box_layout = QHBoxLayout()
        box_layout.setContentsMargins(0, 0, 0, 0)
        box_layout.addWidget(self.move_button)
        self.widget_container.setLayout(box_layout)
        index = self.move_stack.addWidget(self.widget_container)
        self.move_stack.setCurrentIndex(index)
        self.move_game_pop_up.move_clicked.connect(self.move_button.menu().close)
        self.move_game_pop_up.move_clicked.connect(self.move_game)
        self.move_game_pop_up.browse_done.connect(self.show_menu_after_browse)

    def uninstall(self):
        if self.game_utils.uninstall_game(self.game.app_name):
            self.game_utils.update_list.emit(self.game.app_name)
            self.uninstalled.emit(self.game.app_name)

    def repair(self):
        repair_file = os.path.join(self.core.lgd.get_tmp_path(), f"{self.game.app_name}.repair")
        if not os.path.exists(repair_file):
            QMessageBox.warning(
                self,
                "Warning",
                self.tr(
                    "Repair file does not exist or game does not need a repair. Please verify game first"
                ),
            )
            return
        self.signals.install_game.emit(
            InstallOptionsModel(app_name=self.game.app_name, repair=True, update=True)
        )

    def verify(self):
        if not os.path.exists(self.igame.install_path):
            logger.error("Path does not exist")
            QMessageBox.warning(
                self,
                "Warning",
                self.tr("Installation path of {} does not exist. Cannot verify").format(self.igame.title),
            )
            return
        self.verify_widget.setCurrentIndex(1)
        verify_worker = VerifyWorker(self.game.app_name)
        verify_worker.signals.status.connect(self.verify_statistics)
        verify_worker.signals.summary.connect(self.finish_verify)
        self.verify_progress.setValue(0)
        self.verify_threads[self.game.app_name] = verify_worker
        self.verify_pool.start(verify_worker)
        self.move_button.setEnabled(False)

    def verify_statistics(self, num, total, app_name):
        # checked, max, app_name
        if app_name == self.game.app_name:
            self.verify_progress.setValue(num * 100 // total)

    def finish_verify(self, failed, missing, app_name):
        if failed == missing == 0:
            QMessageBox.information(
                self,
                "Summary",
                "Game was verified successfully. No missing or corrupt files found",
            )
            igame = self.core.get_installed_game(app_name)
            if igame.needs_verification:
                igame.needs_verification = False
                self.core.lgd.set_installed_game(self.igame.app_name, igame)
                self.verification_finished.emit(igame)
        elif failed == missing == -1:
            QMessageBox.warning(self, "Warning", self.tr("Something went wrong"))

        else:
            ans = QMessageBox.question(
                self,
                "Summary",
                self.tr(
                    "Verification failed, {} file(s) corrupted, {} file(s) are missing. Do you want to repair them?"
                ).format(failed, missing),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if ans == QMessageBox.Yes:
                self.signals.install_game.emit(
                    InstallOptionsModel(app_name=self.game.app_name, repair=True, update=True)
                )
        self.verify_widget.setCurrentIndex(0)
        self.verify_threads.pop(app_name)
        self.move_button.setEnabled(True)
        self.verify_button.setEnabled(True)

    @pyqtSlot(str)
    def move_game(self, dest_path):
        dest_path = Path(dest_path)
        install_path = Path(self.igame.install_path)
        self.dest_path_with_suffix = dest_path.joinpath(install_path.stem)

        if self.dest_path_with_suffix.is_dir():
            self.existing_game_dir = is_game_dir(install_path, self.dest_path_with_suffix)

        if not self.existing_game_dir:
            for i in dest_path.iterdir():
                if install_path.stem in i.stem:
                    warn_msg = QMessageBox()
                    warn_msg.setText(self.tr("Destination file/directory exists."))
                    warn_msg.setInformativeText(
                        self.tr("Do you really want to overwrite it? This will delete {}").format(
                            self.dest_path_with_suffix
                        )
                    )
                    warn_msg.addButton(QPushButton(self.tr("Yes")), QMessageBox.YesRole)
                    warn_msg.addButton(QPushButton(self.tr("No")), QMessageBox.NoRole)

                    response = warn_msg.exec()

                    if response == 0:
                        # Not using pathlib, since we can't delete not-empty folders. With shutil we can.
                        if self.dest_path_with_suffix.is_dir():
                            shutil.rmtree(self.dest_path_with_suffix)
                        else:
                            self.dest_path_with_suffix.unlink()
                    else:
                        return

        self.move_stack.addWidget(self.progress_of_moving)
        self.move_stack.setCurrentWidget(self.progress_of_moving)

        self.game_moving = self.igame.app_name
        self.is_moving = True

        self.verify_button.setEnabled(False)

        if self.move_game_pop_up.find_mount(dest_path) != self.move_game_pop_up.find_mount(install_path):
            # Destination dir on different drive
            self.start_copy_diff_drive()
        else:
            # Destination dir on same drive
            shutil.move(self.igame.install_path, dest_path)
            self.set_new_game(self.dest_path_with_suffix)

    def update_progressbar(self, progress_int):
        self.progress_of_moving.setValue(progress_int)

    def start_copy_diff_drive(self):
        copy_worker = CopyGameInstallation(
            install_path=self.igame.install_path,
            dest_path=self.dest_path_with_suffix,
            is_existing_dir=self.existing_game_dir,
            igame=self.igame,
        )

        copy_worker.signals.progress.connect(self.update_progressbar)
        copy_worker.signals.finished.connect(self.set_new_game)
        copy_worker.signals.no_space_left.connect(self.warn_no_space_left)
        QThreadPool.globalInstance().start(copy_worker)

    def move_helper_clean_up(self):
        self.move_stack.setCurrentWidget(self.move_button)
        self.move_game_pop_up.refresh_indicator()
        self.is_moving = False
        self.game_moving = None
        self.verify_button.setEnabled(True)
        self.move_button.setEnabled(True)

    # This func does the needed UI changes, e.g. changing back to the initial move tool button and other stuff
    def warn_no_space_left(self):
        err_msg = QMessageBox()
        err_msg.setText(self.tr("Out of space or unknown OS error occured."))
        err_msg.exec()
        self.move_helper_clean_up()

    # Sets all needed variables to the new path.
    def set_new_game(self, dest_path_with_suffix):
        self.install_path.setText(str(dest_path_with_suffix))
        self.igame.install_path = str(dest_path_with_suffix)
        self.core.lgd.set_installed_game(self.igame.app_name, self.igame)
        self.move_game_pop_up.install_path = self.igame.install_path

        self.move_helper_clean_up()

    # We need to re-show the menu, as after clicking on browse, the whole menu gets closed.
    # Otherwise, the user would need to click on the move button again to open it again.
    def show_menu_after_browse(self):
        self.move_button.showMenu()

    def update_game(self, app_name: str):
        self.game = self.core.get_game(app_name)
        self.igame = self.core.get_installed_game(self.game.app_name)
        self.title.setTitle(self.game.app_title)

        pixmap = get_pixmap(self.game.app_name)
        if pixmap.isNull():
            pixmap = get_pixmap(self.parent().parent().parent().ue_name)
        w = 200
        pixmap = pixmap.scaled(w, int(w * 4 / 3))
        self.image.setPixmap(pixmap)

        self.app_name.setText(self.game.app_name)
        if self.igame:
            self.version.setText(self.igame.version)
        else:
            self.version.setText(self.game.app_version(self.igame.platform if self.igame else "Windows"))
        self.dev.setText(self.game.metadata["developer"])

        if self.igame:
            self.install_size.setText(get_size(self.igame.install_size))
            self.install_path.setText(self.igame.install_path)
            self.install_size.setVisible(True)
            self.install_path.setVisible(True)
            self.platform.setText(self.igame.platform)
        else:
            self.install_size.setVisible(False)
            self.install_path.setVisible(False)
            self.platform.setText("Windows")

        if not self.igame:
            # origin game
            self.uninstall_button.setDisabled(True)
            self.verify_button.setDisabled(True)
            self.repair_button.setDisabled(True)
            self.game_actions_stack.setCurrentIndex(1)
        else:
            self.uninstall_button.setDisabled(False)
            self.verify_button.setDisabled(False)
            if not self.args.offline:
                self.repair_button.setDisabled(False)
            self.game_actions_stack.setCurrentIndex(0)

        try:
            is_ue = self.core.get_asset(app_name).namespace == "ue"
        except ValueError:
            is_ue = False
        self.grade.setVisible(not is_ue)
        self.lbl_grade.setVisible(not is_ue)

        if platform.system() != "Windows" and not is_ue:
            self.grade.setText(self.tr("Loading"))
            self.steam_worker.set_app_name(self.game.app_name)
            QThreadPool.globalInstance().start(self.steam_worker)

        if len(self.verify_threads.keys()) == 0 or not self.verify_threads.get(self.game.app_name):
            self.verify_widget.setCurrentIndex(0)
        elif self.verify_threads.get(self.game.app_name):
            self.verify_widget.setCurrentIndex(1)
            self.verify_progress.setValue(
                int(
                    self.verify_threads[self.game.app_name].num
                    / self.verify_threads[self.game.app_name].total
                    * 100
                )
            )

        # If the game that is currently moving matches with the current app_name, we show the progressbar.
        # Otherwhise, we show the move tool button.
        if self.igame is not None:
            if self.game_moving == self.igame.app_name:
                index = self.move_stack.addWidget(self.progress_of_moving)
                self.move_stack.setCurrentIndex(index)
            else:
                index = self.move_stack.addWidget(self.move_button)
                self.move_stack.setCurrentIndex(index)

        # If a game is verifying or moving, disable both verify and moving buttons.
        if len(self.verify_threads):
            self.verify_button.setEnabled(False)
            self.move_button.setEnabled(False)
        if self.is_moving:
            self.move_button.setEnabled(False)
            self.verify_button.setEnabled(False)

        self.move_game_pop_up.update_game(app_name)


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
        stat = os.statvfs(dest_path)
        free_space_dest_drive = stat.f_bavail * stat.f_frsize
        source_size = sum(f.stat().st_size for f in install_path.glob("**/*") if f.is_file())

        # Calculate from bytes to gigabytes
        free_space_dest_drive = round(free_space_dest_drive / 1000**3, 2)
        source_size = round(source_size / 1000**3, 2)
        self.aval_space_label.setText(self.tr("Available space on disk: {}GB".format(free_space_dest_drive)))
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
        igame = self.core.get_installed_game(app_name, False)
        if igame is None:
            return
        self.install_path = igame.install_path
        self.move_path_edit.setText(igame.install_path)
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
        install_path: Path,
        dest_path: Path,
        is_existing_dir: bool,
        igame: InstalledGame,
    ):
        super(CopyGameInstallation, self).__init__()
        self.signals = CopyGameInstallation.Signals()
        self.install_path = str(install_path)
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

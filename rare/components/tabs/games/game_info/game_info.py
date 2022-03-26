import os
import platform
import shutil
from pathlib import Path
from logging import getLogger

from PyQt5.QtCore import pyqtSignal, QThreadPool, pyqtSlot
from PyQt5.QtWidgets import QCheckBox, QFileDialog, QHBoxLayout, QMenu, QProgressBar, QPushButton, QVBoxLayout, QWidget, \
    QMessageBox, QWidgetAction, QSizePolicy

from legendary.models.game import Game, InstalledGame
from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton, ArgumentsSingleton
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
        self.widget_container = QWidget()
        box_layout = QHBoxLayout()
        box_layout.setContentsMargins(0, 0, 0, 0)
        box_layout.addWidget(self.move_button)
        self.widget_container.setLayout(box_layout)
        index = self.move_stack.addWidget(self.widget_container)
        self.move_stack.setCurrentIndex(index)
        self.move_game_pop_up.move_clicked.connect(self.move_game)

    def uninstall(self):
        if self.game_utils.uninstall_game(self.game.app_name):
            self.game_utils.update_list.emit(self.game.app_name)
            self.uninstalled.emit(self.game.app_name)

    def repair(self):
        repair_file = os.path.join(
            self.core.lgd.get_tmp_path(), f"{self.game.app_name}.repair"
        )
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
                self.tr("Installation path of {} does not exist. Cannot verify").format(
                    self.igame.title
                ),
            )
            return
        self.verify_widget.setCurrentIndex(1)
        verify_worker = VerifyWorker(self.game.app_name)
        verify_worker.signals.status.connect(self.verify_staistics)
        verify_worker.signals.summary.connect(self.finish_verify)
        self.verify_progress.setValue(0)
        self.verify_threads[self.game.app_name] = verify_worker
        self.verify_pool.start(verify_worker)

    def verify_staistics(self, num, total, app_name):
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
                    InstallOptionsModel(
                        app_name=self.game.app_name, repair=True, update=True
                    )
                )
        self.verify_widget.setCurrentIndex(0)
        self.verify_threads.pop(app_name)
    
    @pyqtSlot(str)
    def move_game(self, destination_path):
        if Path(destination_path).is_dir():
            destination_path_with_suffix = Path(f'{destination_path}/{self.igame.install_path.split("/")[-1]}')
            if self.move_game_pop_up.create_subfolder_checkbox.checkState() == 2:
                # user wants us to create a subfolder.
                if not destination_path_with_suffix.is_dir():
                    destination_path_with_suffix.mkdir()
                destination_path = str(destination_path_with_suffix)

            progress_of_moving = QProgressBar(self)
            progress_of_moving.setValue(0)

            file_names = os.listdir(self.igame.install_path)

            for file_name in file_names:
                shutil.move(
                    os.path.join(self.igame.install_path, file_name), destination_path
                )
            shutil.rmtree(self.igame.install_path)
            self.install_path.setText(destination_path)
            self.igame.install_path = destination_path
            self.core.lgd.set_installed_game(self.igame.app_name, self.igame)

            progress_of_moving.setValue(100)

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
            self.version.setText(
                self.game.app_version(self.igame.platform if self.igame else "Windows")
            )
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

        if len(self.verify_threads.keys()) == 0 or not self.verify_threads.get(
                self.game.app_name
        ):
            self.verify_widget.setCurrentIndex(0)
        elif self.verify_threads.get(self.game.app_name):
            self.verify_widget.setCurrentIndex(1)
            self.verify_progress.setValue(
                int(self.verify_threads[self.game.app_name].num
                    / self.verify_threads[self.game.app_name].total
                    * 100)
            )
        self.move_game_pop_up.update_game(app_name)


class MoveGamePopUp(QWidget):
    move_clicked = pyqtSignal(str)

    def __init__(self):
        super(MoveGamePopUp, self).__init__()
        layout: QVBoxLayout = QVBoxLayout()
        self.install_path = str()
        self.core = LegendaryCoreSingleton()
        self.move_path_edit = PathEdit(
            str(),
            QFileDialog.Directory,
            edit_func=self.edit_func_move_game
        )
        self.move_game = QPushButton(self.tr("Move"))
        self.move_game.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.move_game.clicked.connect(self.emit_signal)

        self.create_subfolder_checkbox = QCheckBox()
        self.create_subfolder_checkbox.setChecked(True)
        self.create_subfolder_checkbox.stateChanged.connect(self.refresh_indicator)

        layout.addWidget(self.move_path_edit)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.create_subfolder_checkbox, stretch=1)
        button_layout.addWidget(self.move_game)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def emit_signal(self):
        self.move_clicked.emit(self.move_path_edit.text())

    def refresh_indicator(self):
        text = self.move_path_edit.text()
        self.move_path_edit.setText(str())
        self.move_path_edit.setText(text)

    # Thanks to lk.
    def find_mount(self, path):
        mount_point = path
        while path != path.anchor:
            if path.is_mount():
                return path
            else:
                path = path.parent
        return mount_point

    def edit_func_move_game(self, text):
        if not self.install_path or not text:
            self.move_game.setEnabled(False)
            return False, str(), self.tr("You need to provide a directory.")

        destination_path = Path(text)
        current_path = Path(self.install_path)

        destination_path_with_suffix = Path(f'{text}/{self.install_path.split("/")[-1]}')
        if destination_path_with_suffix.is_dir() and len(list(destination_path_with_suffix.iterdir())) > 0 and self.create_subfolder_checkbox.checkState() == 0:
            self.move_game.setEnabled(False)
            return False, text, self.tr("Directory already exists")

        if destination_path == current_path:
            self.move_game.setEnabled(False)
            return False, text, self.tr("You need to select a different directory than the current one.")

        if destination_path_with_suffix.is_dir() and len(list(destination_path_with_suffix.iterdir())) and self.create_subfolder_checkbox.checkState() == 2:
            self.move_game.setEnabled(False)
            return False, text, self.tr("Destination path contains files.")

        if not destination_path.is_dir():
            self.move_game.setEnabled(False)
            return False, text, self.tr("Directory doesn't exist or file selected.")

        if not os.access(text, os.W_OK):
            self.move_game.setEnabled(False)
            return False, text, self.tr("No write permission on destination path.")

        if self.create_subfolder_checkbox.checkState() == 0:
            if len(list(destination_path.iterdir())):
                self.move_game.setEnabled(False)
                return False, text, self.tr("Destination path contains files.")

        if not platform.system() == "Windows":
            if self.find_mount(destination_path) != self.find_mount(current_path):
                self.move_game.setEnabled(False)
                return False, text, self.tr("Moving to a different drive is currently not supported.")
            else:
                self.move_game.setEnabled(True)
                return True, text, str()
        else:
            if current_path.drive != destination_path.drive:
                self.move_game.setEnabled(False)
                return False, text, self.tr("Moving to a different drive is currently not supported.")
    
    def update_game(self, app_name):
        igame = self.core.get_installed_game(app_name, False)
        if igame is None:
            return
        self.install_path = igame.install_path
        self.move_path_edit.setText(igame.install_path)
        self.create_subfolder_checkbox.setText(self.tr("Create '{}' subfolder").format(self.install_path.split("/")[-1]))

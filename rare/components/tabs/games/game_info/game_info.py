import os
import platform
import shutil
from logging import getLogger
from pathlib import Path

from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
    QThreadPool,
    pyqtSlot,
)
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QMenu,
    QProgressBar,
    QPushButton,
    QWidget,
    QMessageBox,
    QWidgetAction,
)
from legendary.models.game import Game, InstalledGame

from rare.models.install import InstallOptionsModel
from rare.shared import (
    LegendaryCoreSingleton,
    GlobalSignalsSingleton,
    ArgumentsSingleton,
)
from rare.shared import ImageManagerSingleton
from rare.shared.image_manager import ImageSize
from rare.ui.components.tabs.games.game_info.game_info import Ui_GameInfo
from rare.utils.legendary_utils import VerifyWorker
from rare.utils.misc import get_size
from rare.utils.steam_grades import SteamWorker
from rare.widgets.image_widget import ImageWidget
from .move_game import CopyGameInstallation, MoveGamePopUp, is_game_dir

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
        self.image_manager = ImageManagerSingleton()
        self.game_utils = game_utils

        self.image = ImageWidget(self)
        self.image.setFixedSize(ImageSize.Display)
        self.layout_game_info.insertWidget(0, self.image, alignment=Qt.AlignTop)

        if platform.system() == "Windows":
            self.lbl_grade.setVisible(False)
            self.grade.setVisible(False)
        else:
            self.steam_worker: SteamWorker = SteamWorker(self.core)
            self.steam_worker.signals.rating.connect(self.grade.setText)
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

    @pyqtSlot()
    def repair(self):
        """ This function is to be called from the button only """
        repair_file = os.path.join(self.core.lgd.get_tmp_path(), f"{self.igame.app_name}.repair")
        if not os.path.exists(repair_file):
            QMessageBox.warning(
                self,
                self.tr("Error - {}").format(self.igame.title),
                self.tr(
                    "Repair file does not exist or game does not need a repair. Please verify game first"
                ),
            )
            return
        self.repair_game(self.igame)

    def repair_game(self, igame: InstalledGame):
        game = self.core.get_game(igame.app_name)
        ans = False
        if igame.version != game.app_version(igame.platform):
            ans = QMessageBox.question(
                self,
                self.tr("Repair and update?"),
                self.tr(
                    "There is an update for <b>{}</b> from <b>{}</b> to <b>{}</b>."
                    "Do you want to update the game while repairing it?"
                ).format(igame.title, igame.version, game.app_version(igame.platform)),
            ) == QMessageBox.Yes
        self.signals.install_game.emit(
            InstallOptionsModel(
                app_name=igame.app_name, repair_mode=True, repair_and_update=ans, update=True
            )
        )

    @pyqtSlot()
    def verify(self):
        """ This function is to be called from the button only """
        if not os.path.exists(self.igame.install_path):
            logger.error(f"Installation path {self.igame.install_path} for {self.igame.title} does not exist")
            QMessageBox.warning(
                self,
                self.tr("Error - {}").format(self.igame.title),
                self.tr("Installation path for <b>{}</b> does not exist. Cannot continue.").format(self.igame.title),
            )
            return
        self.verify_game(self.igame)

    def verify_game(self, igame: InstalledGame):
        self.verify_widget.setCurrentIndex(1)
        verify_worker = VerifyWorker(igame.app_name)
        verify_worker.signals.status.connect(self.verify_status)
        verify_worker.signals.result.connect(self.verify_result)
        verify_worker.signals.error.connect(self.verify_error)
        self.verify_progress.setValue(0)
        self.verify_threads[igame.app_name] = verify_worker
        self.verify_pool.start(verify_worker)
        self.move_button.setEnabled(False)

    def verify_cleanup(self, app_name: str):
        self.verify_widget.setCurrentIndex(0)
        self.verify_threads.pop(app_name)
        self.move_button.setEnabled(True)
        self.verify_button.setEnabled(True)

    @pyqtSlot(str, str)
    def verify_error(self, app_name, message):
        self.verify_cleanup(app_name)
        igame = self.core.get_installed_game(app_name)
        QMessageBox.warning(
            self,
            self.tr("Error - {}").format(igame.title),
            message
        )

    @pyqtSlot(str, int, int, float, float)
    def verify_status(self, app_name, num, total, percentage, speed):
        # checked, max, app_name
        if app_name == self.game.app_name:
            self.verify_progress.setValue(num * 100 // total)

    @pyqtSlot(str, bool, int, int)
    def verify_result(self, app_name, success, failed, missing):
        self.verify_cleanup(app_name)
        self.repair_button.setDisabled(success)
        igame = self.core.get_installed_game(app_name)
        if success:
            QMessageBox.information(
                self,
                self.tr("Summary - {}").format(igame.title),
                self.tr("<b>{}</b> has been verified successfully. "
                        "No missing or corrupt files found").format(igame.title),
            )
            self.verification_finished.emit(igame)
        else:
            ans = QMessageBox.question(
                self,
                self.tr("Summary - {}").format(igame.title),
                self.tr(
                    "Verification failed, <b>{}</b> file(s) corrupted, <b>{}</b> file(s) are missing. "
                    "Do you want to repair them?"
                ).format(failed, missing),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if ans == QMessageBox.Yes:
                self.repair_game(igame)

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

        self.image.setPixmap(self.image_manager.get_pixmap(self.game.app_name, color=True))

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
                self.repair_button.setDisabled(
                    not os.path.exists(os.path.join(self.core.lgd.get_tmp_path(), f"{self.igame.app_name}.repair"))
                )
            self.game_actions_stack.setCurrentIndex(0)

        try:
            is_ue = self.core.get_asset(app_name).namespace == "ue"
        except ValueError:
            is_ue = False
        grade_visible = not is_ue and platform.system() != "Windows"
        self.grade.setVisible(grade_visible)
        self.lbl_grade.setVisible(grade_visible)

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


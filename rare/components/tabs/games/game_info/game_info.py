import os
import platform

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QMessageBox

from legendary.core import LegendaryCore
from legendary.models.game import Game, InstalledGame
from rare.ui.components.tabs.games.game_info.game_info import Ui_GameInfo
from rare.utils.legendary_utils import VerifyThread
from rare.utils.steam_grades import SteamWorker
from rare.utils.utils import get_size, get_pixmap


class GameInfo(QWidget, Ui_GameInfo):
    igame: InstalledGame
    game: Game
    uninstall_game = pyqtSignal(str)
    update_list = pyqtSignal(str)
    verify_game = pyqtSignal(str)
    verify_threads = {}

    def __init__(self, core: LegendaryCore, parent):
        super(GameInfo, self).__init__(parent=parent)
        self.setupUi(self)
        self.core = core

        if platform.system() == "Windows":
            self.lbl_grade.setVisible(False)
            self.grade.setVisible(False)
        else:
            self.steam_worker = SteamWorker(self.core)
            self.steam_worker.rating_signal.connect(self.grade.setText)

        self.game_actions_stack.setCurrentIndex(0)
        self.game_actions_stack.resize(self.game_actions_stack.minimumSize())

        self.uninstall_button.clicked.connect(self.uninstall)
        self.verify_button.clicked.connect(self.verify)
        self.repair_button.clicked.connect(self.repair)

    def uninstall(self):
        self.uninstall_game.emit(self.game.app_name)
        self.update_list.emit(self.game.app_name)

    def repair(self):
        repair_file = os.path.join(self.core.lgd.get_tmp_path(), f'{self.game.app_name}.repair')
        if not os.path.exists(repair_file):
            QMessageBox.warning(self, "Warning", self.tr(
                "Repair file does not exist or game does not need a repair. Please verify game first"))
            return
        self.verify_game.emit(self.game.app_name)

    def verify(self):
        self.verify_widget.setCurrentIndex(1)
        verify_thread = VerifyThread(self.core, self.game.app_name)
        verify_thread.status.connect(self.verify_satistics)
        verify_thread.summary.connect(self.finish_verify)
        verify_thread.start()
        self.verify_progress.setValue(0)
        self.verify_threads[self.game.app_name] = verify_thread

    def verify_satistics(self, progress):
        # checked, max, app_name
        if progress[2] == self.game.app_name:
            self.verify_progress.setValue(progress[0] * 100 / progress[1])

    def finish_verify(self, failed):
        failed, missing, app_name = failed
        if failed == 0 and missing == 0:
            QMessageBox.information(self, "Summary",
                                    "Game was verified successfully. No missing or corrupt files found")
        else:
            ans = QMessageBox.question(self, "Summary", self.tr(
                'Verification failed, {} file(s) corrupted, {} file(s) are missing. Do you want to repair them?').format(
                failed, missing), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if ans == QMessageBox.Yes:
                self.verify_game.emit(self.game.app_name)
        self.verify_widget.setCurrentIndex(0)
        self.verify_threads.pop(app_name)

    def update_game(self, game: Game):
        self.game = game
        self.igame = self.core.get_installed_game(game.app_name)
        self.game_title.setText(f'<h2>{self.game.app_title}</h2>')

        pixmap = get_pixmap(game.app_name)
        w = 200
        pixmap = pixmap.scaled(w, int(w * 4 / 3))
        self.image.setPixmap(pixmap)

        self.app_name.setText(self.game.app_name)
        self.version.setText(self.game.app_version)
        self.dev.setText(self.game.metadata["developer"])
        if self.igame:
            self.install_size.setText(get_size(self.igame.install_size))
            self.install_path.setText(self.igame.install_path)
            self.install_size.setVisible(True)
            self.install_path.setVisible(True)
        else:
            self.install_size.setVisible(False)
            self.install_path.setVisible(False)

        if platform.system() != "Windows":
            self.grade.setText(self.tr("Loading"))
            self.steam_worker.set_app_name(game.app_name)
            self.steam_worker.start()

        if len(self.verify_threads.keys()) == 0 or not self.verify_threads.get(game.app_name):
            self.verify_widget.setCurrentIndex(0)
        elif self.verify_threads.get(game.app_name):
            self.verify_widget.setCurrentIndex(1)
            self.verify_progress.setValue(
                self.verify_threads[game.app_name].num / self.verify_threads[game.app_name].total * 100
            )

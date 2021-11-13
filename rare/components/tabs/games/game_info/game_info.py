import os
import platform

from PyQt5.QtCore import pyqtSignal, QThreadPool
from PyQt5.QtWidgets import QWidget, QMessageBox

from legendary.models.game import Game, InstalledGame
from rare import shared
from rare.ui.components.tabs.games.game_info.game_info import Ui_GameInfo
from rare.utils.extra_widgets import CustomQMessageDialog
from rare.utils.legendary_utils import VerifyWorker
from rare.utils.models import InstallOptionsModel
from rare.utils.steam_grades import SteamWorker
from rare.utils.utils import get_size, get_pixmap


class GameInfo(QWidget, Ui_GameInfo):
    igame: InstalledGame
    game: Game = None
    verify_threads = dict()
    verification_finished = pyqtSignal(InstalledGame)
    uninstalled = pyqtSignal(Game)

    def __init__(self, parent):
        super(GameInfo, self).__init__(parent=parent)
        self.setupUi(self)
        self.core = shared.core
        self.signals = shared.signals

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

        self.uninstall_button.clicked.connect(lambda: self.signals.uninstall_game.emit(self.game))
        self.verify_button.clicked.connect(self.verify)
        self.repair_button.clicked.connect(self.repair)

        self.verify_pool = QThreadPool()
        self.verify_pool.setMaxThreadCount(2)

    def repair(self):
        repair_file = os.path.join(self.core.lgd.get_tmp_path(), f'{self.game.app_name}.repair')
        if not os.path.exists(repair_file):
            QMessageBox.warning(self, "Warning", self.tr(
                "Repair file does not exist or game does not need a repair. Please verify game first"))
            return
        self.signals.install_game.emit(InstallOptionsModel(app_name=self.game.app_name, repair=True,
                                                           update=True))

    def verify(self):
        self.verify_widget.setCurrentIndex(1)
        verify_worker = VerifyWorker(self.core, self.game.app_name)
        verify_worker.signals.status.connect(self.verify_staistics)
        verify_worker.signals.summary.connect(self.finish_verify)
        self.verify_pool.start(verify_worker)
        self.verify_progress.setValue(0)
        self.verify_threads[self.game.app_name] = verify_worker
        self.verify_pool.start(verify_worker)

    def verify_staistics(self, progress):
        # checked, max, app_name
        if progress[2] == self.game.app_name:
            self.verify_progress.setValue(progress[0] * 100 // progress[1])

    def finish_verify(self, failed, missing, app_name):
        if failed == missing == 0:
            QMessageBox.information(self, "Summary",
                                    "Game was verified successfully. No missing or corrupt files found")
            igame = self.core.get_installed_game(app_name)
            if igame.needs_verification:
                igame.needs_verification = False
                self.core.lgd.set_installed_game(self.igame.app_name, igame)
                self.verification_finished.emit(igame)
        else:
            ans = CustomQMessageDialog.yes_no_question(self, "Summary", self.tr(
                'Verification failed, {} file(s) corrupted, {} file(s) are missing. Do you want to repair them?').format(
                failed, missing))
            if ans == CustomQMessageDialog.yes:
                self.signals.install_game.emit(InstallOptionsModel(app_name=self.game.app_name, repair=True,
                                                                   update=True))
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

        if not self.igame:
            # origin game
            self.uninstall_button.setDisabled(True)
            self.verify_button.setDisabled(True)
            self.repair_button.setDisabled(True)
            self.game_actions_stack.setCurrentIndex(1)
        else:
            self.uninstall_button.setDisabled(False)
            self.verify_button.setDisabled(False)
            self.repair_button.setDisabled(False)
            self.game_actions_stack.setCurrentIndex(0)

        if platform.system() != "Windows":
            self.grade.setText(self.tr("Loading"))
            self.steam_worker.set_app_name(game.app_name)
            QThreadPool.globalInstance().start(self.steam_worker)

        if len(self.verify_threads.keys()) == 0 or not self.verify_threads.get(game.app_name):
            self.verify_widget.setCurrentIndex(0)
        elif self.verify_threads.get(game.app_name):
            self.verify_widget.setCurrentIndex(1)
            self.verify_progress.setValue(
                self.verify_threads[game.app_name].num / self.verify_threads[game.app_name].total * 100
            )

import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QKeyEvent
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout, QTabWidget, QMessageBox, \
    QProgressBar, QStackedWidget
from legendary.core import LegendaryCore
from legendary.models.game import InstalledGame, Game
from qtawesome import icon

from Rare.Components.Tabs.Games.GameInfo.GameSettings import GameSettings
from Rare.utils import LegendaryApi
from Rare.utils.LegendaryApi import VerifyThread
from Rare.utils.QtExtensions import SideTabBar
from Rare.utils.utils import IMAGE_DIR


class InfoTabs(QTabWidget):
    def __init__(self, core):
        super(InfoTabs, self).__init__()
        self.app_name = ""
        self.core = core
        self.setTabBar(SideTabBar())
        self.setTabPosition(QTabWidget.West)

        self.addTab(QWidget(), icon("mdi.keyboard-backspace", color="white"), self.tr("Back"))
        self.tabBarClicked.connect(lambda x: self.parent().layout.setCurrentIndex(0) if x == 0 else None)

        self.info = GameInfo(core)
        self.addTab(self.info, self.tr("Game Info"))
        self.settings = GameSettings(core)
        self.addTab(self.settings, self.tr("Settings"))
        self.tabBar().setCurrentIndex(1)

    def update_game(self, app_name):
        self.info.update_game(app_name)
        self.settings.update_game(app_name)

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() == Qt.Key_Escape:
            self.parent().layout.setCurrentIndex(0)


class GameInfo(QWidget):
    igame: InstalledGame
    game: Game
    update_list = pyqtSignal()
    verify_game = pyqtSignal(str)

    def __init__(self, core: LegendaryCore):
        super(GameInfo, self).__init__()
        self.core = core
        self.layout = QVBoxLayout()

        # TODO More Information: Image text settings needs_verification platform
        top_layout = QHBoxLayout()

        self.image = QLabel()
        top_layout.addWidget(self.image)

        right_layout = QVBoxLayout()
        self.game_title = QLabel("Error")
        self.game_title.setTextInteractionFlags(Qt.TextSelectableByMouse)
        right_layout.addWidget(self.game_title)

        self.dev = QLabel("Error")
        right_layout.addWidget(self.dev)

        self.app_name = QLabel("Error")
        self.app_name.setTextInteractionFlags(Qt.TextSelectableByMouse)
        right_layout.addWidget(self.app_name)

        self.version = QLabel("Error")
        right_layout.addWidget(self.version)

        self.install_size = QLabel("Error")
        right_layout.addWidget(self.install_size)

        self.install_path = QLabel("Error")
        right_layout.addWidget(self.install_path)

        top_layout.addLayout(right_layout)
        top_layout.addStretch()

        self.game_actions = GameActions()

        self.game_actions.uninstall_button.clicked.connect(self.uninstall)
        self.game_actions.verify_button.clicked.connect(self.verify)
        self.game_actions.repair_button.clicked.connect(self.repair)

        self.layout.addLayout(top_layout)
        self.layout.addWidget(self.game_actions)
        self.layout.addStretch()
        self.setLayout(self.layout)

    def uninstall(self):
        if QMessageBox.question(self, "Uninstall", self.tr("Are you sure to uninstall " + self.game.app_title),
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            LegendaryApi.uninstall(self.game.app_name, self.core)
            self.update_list.emit()

    def repair(self):
        repair_file = os.path.join(self.core.lgd.get_tmp_path(), f'{self.game.app_name}.repair')
        if not os.path.exists(repair_file):
            QMessageBox.warning(self, "Warning", self.tr(
                "Repair file does not exist or game does not need a repair. Please verify game first"))
            return
        self.verify_game.emit(self.game.app_name)

    def verify(self):
        self.game_actions.verify_widget.setCurrentIndex(1)
        self.verify_thread = VerifyThread(self.core, self.game.app_name)
        self.verify_thread.status.connect(lambda x: self.game_actions.verify_progress_bar.setValue(x[0] * 100 / x[1]))
        self.verify_thread.summary.connect(self.finish_verify)
        self.verify_thread.start()

    def finish_verify(self, failed):
        failed, missing = failed
        if failed == 0 and missing == 0:
            QMessageBox.information(self, "Summary",
                                    "Game was verified successfully. No missing or corrupt files found")
        else:
            ans = QMessageBox.question(self, "Summary", self.tr(
                'Verification failed, {} file(s) corrupted, {} file(s) are missing. Do you want to repair them?').format(
                failed, missing), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if ans == QMessageBox.Yes:
                self.verify_game.emit(self.game.app_name)
        self.game_actions.verify_widget.setCurrentIndex(0)

    def update_game(self, app_name):
        self.game = self.core.get_game(app_name)
        self.igame = self.core.get_installed_game(app_name)

        self.game_title.setText(f"<h2>{self.game.app_title}</h2>")

        if os.path.exists(f"{IMAGE_DIR}/{self.game.app_name}/FinalArt.png"):
            pixmap = QPixmap(f"{IMAGE_DIR}/{self.game.app_name}/FinalArt.png")
        elif os.path.exists(f"{IMAGE_DIR}/{self.game.app_name}/DieselGameBoxTall.png"):
            pixmap = QPixmap(f"{IMAGE_DIR}/{self.game.app_name}/DieselGameBoxTall.png")
        elif os.path.exists(f"{IMAGE_DIR}/{self.game.app_name}/DieselGameBoxLogo.png"):
            pixmap = QPixmap(f"{IMAGE_DIR}/{self.game.app_name}/DieselGameBoxLogo.png")
        else:
            # logger.warning(f"No Image found: {self.game.title}")
            pixmap = None
        if pixmap:
            w = 200
            pixmap = pixmap.scaled(w, int(w * 4 / 3))
            self.image.setPixmap(pixmap)
        self.app_name.setText("App name: " + self.game.app_name)
        self.version.setText("Version: " + self.game.app_version)
        self.dev.setText(self.tr("Developer: ") + self.game.metadata["developer"])
        self.install_size.setText(
            self.tr("Install size: ") + str(round(self.igame.install_size / (1024 ** 3), 2)) + " GB")
        self.install_path.setText(self.tr("Install path: ") + self.igame.install_path)


class GameActions(QWidget):
    def __init__(self):
        super(GameActions, self).__init__()
        self.layout = QVBoxLayout()
        self.game_actions = QLabel("<h3>Game actions</h3>")
        self.layout.addWidget(self.game_actions)

        uninstall_layout = QHBoxLayout()
        self.uninstall_game = QLabel(self.tr("Uninstall game"))
        uninstall_layout.addWidget(self.uninstall_game)
        self.uninstall_button = QPushButton(self.tr("Uninstall"))
        self.uninstall_button.setFixedWidth(250)
        uninstall_layout.addWidget(self.uninstall_button)
        self.layout.addLayout(uninstall_layout)

        verify_layout = QHBoxLayout()
        self.verify_game = QLabel(self.tr("Verify Game"))
        verify_layout.addWidget(self.verify_game)
        self.verify_widget = QStackedWidget()
        self.verify_widget.setMaximumHeight(20)
        self.verify_widget.setFixedWidth(250)
        self.verify_button = QPushButton(self.tr("Verify"))
        self.verify_widget.addWidget(self.verify_button)
        self.verify_progress_bar = QProgressBar()
        self.verify_progress_bar.setMaximum(100)
        self.verify_widget.addWidget(self.verify_progress_bar)
        verify_layout.addWidget(self.verify_widget)
        self.layout.addLayout(verify_layout)

        repair_layout = QHBoxLayout()
        repair_info = QLabel(self.tr("Repair Game"))
        repair_layout.addWidget(repair_info)
        self.repair_button = QPushButton(self.tr("Repair"))
        self.repair_button.setFixedWidth(250)
        repair_layout.addWidget(self.repair_button)
        self.layout.addLayout(repair_layout)

        self.setLayout(self.layout)

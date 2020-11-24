import subprocess
from logging import getLogger

from PyQt5.QtCore import QThread, pyqtSignal, QProcess
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QStyle

from Rare.Dialogs import InstallDialog, GameSettingsDialog
from Rare.utils import legendaryUtils

logger = getLogger("Game")


class Thread(QThread):
    signal = pyqtSignal()

    def __init__(self, proc):
        super(Thread, self).__init__()
        self.proc: subprocess.Popen = proc

    def run(self):
        self.sleep(3)
        logger.info("Running ")
        while True:
            if not self.proc.poll():
                self.sleep(3)
            else:
                self.signal.emit()
                self.quit()
                logger.info("Kill")
                break


class GameWidget(QWidget):
    proc: QProcess
    signal = pyqtSignal(str)

    def __init__(self, game):
        super(GameWidget, self).__init__()
        self.game = game
        self.title = game.title
        self.app_name = game.app_name
        self.version = game.version
        self.size = game.install_size
        self.launch_params = game.launch_parameters
        # self.dev =
        self.game_running = False
        self.layout = QHBoxLayout()

        pixmap = QPixmap(f"../images/{game.app_name}/FinalArt.png")
        pixmap = pixmap.scaled(180, 240)
        self.image = QLabel()
        self.image.setPixmap(pixmap)
        self.layout.addWidget(self.image)

        ##Layout on the right
        self.childLayout = QVBoxLayout()

        play_icon = self.style().standardIcon(getattr(QStyle, 'SP_MediaPlay'))
        settings_icon = self.style().standardIcon(getattr(QStyle, 'SP_DirIcon'))
        self.title_widget = QLabel(f"<h1>{self.title}</h1>")
        self.launch_button = QPushButton(play_icon, "Launch")
        self.launch_button.clicked.connect(self.launch)
        self.wine_rating = QLabel("Wine Rating: " + self.get_rating())
        self.version_label = QLabel("Version: " + str(self.version))
        self.size_label = QLabel(f"Installed size: {round(self.size / (1024 ** 3), 2)} GB")
        self.settings_button = QPushButton(settings_icon, " Settings (Icon TODO)")
        self.settings_button.clicked.connect(self.settings)

        self.childLayout.addWidget(self.title_widget)
        self.childLayout.addWidget(self.launch_button)
        self.childLayout.addWidget(self.wine_rating)
        self.childLayout.addWidget(self.version_label)
        self.childLayout.addWidget(self.size_label)
        self.childLayout.addWidget(self.settings_button)

        self.childLayout.addStretch(1)
        self.layout.addLayout(self.childLayout)
        self.setLayout(self.layout)

    def launch(self):
        if not self.game_running:
            logger.info(f"launching {self.title}")
            self.proc = legendaryUtils.launch_game(self.app_name)
            if not self.proc:
                print("Fail")
                return

            self.proc.finished.connect(self.finished)
            self.launch_button.setText("Kill")
            self.game_running = True

        else:
            self.kill()

    def finished(self, exit_code):
        self.launch_button.setText("Launch")
        logger.info(f"Game {self.title} finished with exit code {exit_code}")
        self.game_running = False

    def kill(self):
        self.proc.kill()
        self.launch_button.setText("Launch")
        self.game_running = False
        logger.info("Killing Game")

    def get_rating(self) -> str:
        return "gold"  # TODO

    def settings(self):
        settings_dialog = GameSettingsDialog(self.game)
        action = settings_dialog.get_settings()
        if action == "uninstall":
            legendaryUtils.uninstall(self.app_name)
            self.signal.emit(self.app_name)


class UninstalledGameWidget(QWidget):
    def __init__(self, game):
        super(UninstalledGameWidget, self).__init__()
        self.title = game.app_title
        self.app_name = game.app_name
        self.version = game.app_version
        self.layout = QHBoxLayout()
        self.game = game

        pixmap = QPixmap(f"../images/{game.app_name}/UninstalledArt.png")
        pixmap = pixmap.scaled(120, 160)
        self.image = QLabel()
        self.image.setPixmap(pixmap)

        self.child_layout = QVBoxLayout()

        self.title_label = QLabel(f"<h2>{self.title}</h2>")
        self.app_name_label = QLabel(f"App Name: {self.app_name}")
        self.version_label = QLabel(f"Version: {self.version}")
        self.install_button = QPushButton("Install")
        self.install_button.clicked.connect(self.install)

        self.child_layout.addWidget(self.title_label)
        self.child_layout.addWidget(self.app_name_label)
        self.child_layout.addWidget(self.version_label)
        self.child_layout.addWidget(self.install_button)
        self.child_layout.addStretch(1)
        self.layout.addWidget(self.image)
        self.layout.addLayout(self.child_layout)

        self.layout.addStretch(1)
        self.setLayout(self.layout)

    def install(self):
        logger.info("install " + self.title)
        dia = InstallDialog(self.game)
        data = dia.get_data()
        if data != 0:
            path = data.get("install_path")
            logger.info(f"install {self.app_name} in path {path}")
            legendaryUtils.install(self.app_name, path=path)

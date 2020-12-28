import os
import subprocess
from logging import getLogger

from PyQt5.QtCore import QThread, pyqtSignal, QProcess
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton

from Rare.Dialogs import InstallDialog
from Rare.utils.RareConfig import IMAGE_DIR

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


class UninstalledGameWidget(QWidget):
    def __init__(self, game):
        super(UninstalledGameWidget, self).__init__()
        self.title = game.app_title
        self.app_name = game.app_name
        self.version = game.app_version
        self.layout = QHBoxLayout()
        self.game = game
        if os.path.exists(f"{IMAGE_DIR}/{game.app_name}/UninstalledArt.png"):
            pixmap = QPixmap(f"{IMAGE_DIR}/{game.app_name}/UninstalledArt.png")
            pixmap = pixmap.scaled(120, 160)
            self.image = QLabel()
            self.image.setPixmap(pixmap)
        else:
            print(os.listdir(IMAGE_DIR) / game.app_name)

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
        print(data)
        if data != 0:
            path = data.get("install_path")
            logger.info(f"install {self.app_name} in path {path}")
            # TODO
            self.proc = QProcess()
            self.proc.finished.connect(self.download_finished)
            self.proc.start("legendary", ["-y", f"--base-path {path}", self.app_name])

            # legendaryUtils.install(self.app_name, path=path)
        else:
            logger.info("Download canceled")

    def download_finished(self):
        self.setVisible(False)
        logger.info("Download finished")

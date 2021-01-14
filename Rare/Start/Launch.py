from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QDialog, QLabel, QProgressBar, QVBoxLayout
from legendary.core import LegendaryCore

from Rare.utils.RareUtils import download_images


class LaunchThread(QThread):
    download_progess = pyqtSignal(int)
    action = pyqtSignal(str)

    def __init__(self, core: LegendaryCore, parent=None):
        super(LaunchThread, self).__init__(parent)
        self.core = core

    def run(self):
        self.action.emit("Login")
        self.action.emit("Downloading Images")
        download_images(self.download_progess, self.core)
        self.action.emit("finish")


class LaunchDialog(QDialog):
    def __init__(self, core: LegendaryCore):
        super(LaunchDialog, self).__init__()

        self.title = QLabel("<h3>"+self.tr("Launching Rare")+"</h3>")
        self.thread = LaunchThread(core, self)
        self.thread.download_progess.connect(self.update_pb)
        self.thread.action.connect(self.info)
        self.info_pb = QProgressBar()
        self.info_pb.setMaximum(len(core.get_game_list()))
        self.info_text = QLabel(self.tr("Logging in"))
        self.layout = QVBoxLayout()

        self.layout.addWidget(self.title)
        self.layout.addWidget(self.info_pb)
        self.layout.addWidget(self.info_text)

        self.setLayout(self.layout)
        self.thread.start()

    def update_pb(self, i: int):
        self.info_pb.setValue(i)

    def info(self, text: str):
        if text == "finish":
            self.close()
        self.info_text.setText(text)

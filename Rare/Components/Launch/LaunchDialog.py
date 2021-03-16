from logging import getLogger

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QDialog, QLabel, QProgressBar, QVBoxLayout
from custom_legendary.core import LegendaryCore

from Rare.Components.Dialogs.Login.LoginDialog import LoginDialog
from Rare.utils.utils import download_images

logger = getLogger("Login")


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


class LoginThread(QThread):
    login = pyqtSignal()
    start_app = pyqtSignal()

    def __init__(self, core: LegendaryCore):
        super(LoginThread, self).__init__()
        self.core = core

    def run(self):
        logger.info("Try if you are logged in")
        try:
            if self.core.login():
                logger.info("You are logged in")
                self.start_app.emit()
            else:
                self.run()
        except ValueError:
            logger.info("You are not logged in. Open Login Window")
            self.login.emit()


class LaunchDialog(QDialog):
    def __init__(self, core: LegendaryCore):
        super(LaunchDialog, self).__init__()
        self.core = core
        self.login_thread = LoginThread(core)
        self.login_thread.login.connect(self.login)
        self.login_thread.start_app.connect(self.launch)
        self.login_thread.start()

        self.title = QLabel("<h3>" + self.tr("Launching Rare") + "</h3>")
        self.info_pb = QProgressBar()
        self.info_text = QLabel(self.tr("Logging in"))
        self.layout = QVBoxLayout()

        self.layout.addWidget(self.title)
        self.layout.addWidget(self.info_pb)
        self.layout.addWidget(self.info_text)

        self.setLayout(self.layout)

    def login(self):
        if LoginDialog(core=self.core).login():
            self.login_thread.start()
        else:
            exit(0)

    def launch(self):
        #self.core = core
        self.info_pb.setMaximum(len(self.core.get_game_list()))
        self.info_text.setText(self.tr("Downloading Images"))
        self.thread = LaunchThread(self.core, self)
        self.thread.download_progess.connect(self.update_pb)
        self.thread.action.connect(self.info)
        self.thread.start()

    def update_pb(self, i: int):
        self.info_pb.setValue(i)

    def info(self, text: str):
        if text == "finish":
            self.close()
        self.info_text.setText(text)

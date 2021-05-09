from logging import getLogger

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QDialog, QLabel, QProgressBar, QVBoxLayout
from requests.exceptions import ConnectionError

from custom_legendary.core import LegendaryCore
from rare.components.dialogs.login import LoginDialog
from rare.utils.utils import download_images

logger = getLogger("Login")


class LaunchThread(QThread):
    download_progess = pyqtSignal(int)
    action = pyqtSignal(str)

    def __init__(self, core: LegendaryCore, parent=None):
        super(LaunchThread, self).__init__(parent)
        self.core = core

    def run(self):
        self.action.emit("Login")
        self.action.emit(self.tr("Downloading Images"))
        download_images(self.download_progess, self.core)
        self.action.emit("finish")


class LoginThread(QThread):
    login = pyqtSignal()
    start_app = pyqtSignal(bool)  # offline

    def __init__(self, core: LegendaryCore):
        super(LoginThread, self).__init__()
        self.core = core

    def run(self):
        logger.info("Try if you are logged in")
        try:
            if self.core.login():
                logger.info("You are logged in")
                self.start_app.emit(False)
            else:
                self.run()
        except ValueError:
            logger.info("You are not logged in. Open Login Window")
            self.login.emit()
        except ConnectionError as e:
            logger.warning(e)
            self.start_app.emit(True)


class LaunchDialog(QDialog):
    start_app = pyqtSignal(bool)

    def __init__(self, core: LegendaryCore, offline):
        super(LaunchDialog, self).__init__()
        self.core = core
        if not offline:
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

        if offline:
            self.launch(offline)

    def login(self):
        self.hide()
        if LoginDialog(core=self.core).login():
            self.show()
            self.login_thread.start()
        else:
            exit(0)

    def launch(self, offline=False):
        # self.core = core
        self.offline = offline
        self.info_text.setText(self.tr("Downloading Images"))
        self.thread = LaunchThread(self.core, self)
        self.thread.download_progess.connect(self.update_pb)
        self.thread.action.connect(self.info)
        self.thread.start()

    def update_pb(self, i: int):
        self.info_pb.setValue(i)

    def info(self, text: str):
        if text == "finish":
            self.info_text.setText(self.tr("Starting..."))
            self.info_pb.setValue(100)
            self.start_app.emit(self.offline)
        else:
            self.info_text.setText(text)

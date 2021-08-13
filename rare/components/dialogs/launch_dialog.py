import os
from logging import getLogger

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import QDialog
from requests.exceptions import ConnectionError

from custom_legendary.core import LegendaryCore
from rare.components.dialogs.login import LoginDialog
from rare.ui.components.dialogs.launch_dialog import Ui_LaunchDialog
from rare.utils.utils import download_images

logger = getLogger("Login")


class ImageThread(QThread):
    download_progess = pyqtSignal(int)

    def __init__(self, core: LegendaryCore, parent=None):
        super(ImageThread, self).__init__(parent)
        self.core = core

    def run(self):
        download_images(self.download_progess, self.core)
        self.download_progess.emit(100)


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


class LaunchDialog(QDialog, Ui_LaunchDialog):
    start_app = pyqtSignal(bool)
    finished = False

    def __init__(self, core: LegendaryCore, offline: bool = False):
        super(LaunchDialog, self).__init__()
        self.setupUi(self)
        self.offline = offline
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        self.core = core
        if not offline:
            self.login_thread = LoginThread(core)
            self.login_thread.login.connect(self.login)
            self.login_thread.start_app.connect(self.launch)
            self.login_thread.start()

        else:
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
        if not os.path.exists(p := os.path.expanduser("~/.cache/rare/images")):
            os.makedirs(p)
        self.offline = offline

        if not offline:

            self.image_info.setText(self.tr("Downloading Images"))
            self.img_thread = ImageThread(self.core, self)
            self.img_thread.download_progess.connect(self.update_image_progbar)
            self.img_thread.finished.connect(self.finish)
            self.img_thread.start()

        else:
            self.finished = True
            self.finish()

    def update_image_progbar(self, i: int):
        self.image_prog_bar.setValue(i)

    def finish(self):
        self.image_info.setText(self.tr("Starting..."))
        self.image_prog_bar.setValue(100)
        self.start_app.emit(self.offline)

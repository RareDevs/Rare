import os
from logging import getLogger

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QDialog
from requests.exceptions import ConnectionError

from custom_legendary.core import LegendaryCore
from rare import image_dir
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


class LaunchDialog(QDialog, Ui_LaunchDialog):
    quit_app = pyqtSignal(int)
    start_app = pyqtSignal(bool)

    def __init__(self, core: LegendaryCore, offline=False, parent=None):
        super(LaunchDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.core = core
        self.offline = offline
        self.image_thread = None

    def login(self):
        do_launch = True
        try:
            if self.offline:
                pass
            else:
                if self.core.login():
                    logger.info("You are logged in")
                else:
                    raise ValueError("You are not logged in. Open Login Window")
        except ValueError as e:
            logger.info(str(e))
            do_launch = LoginDialog(core=self.core, parent=self).login()
        except ConnectionError as e:
            logger.warning(e)
            self.offline = True
        finally:
            if do_launch:
                self.show()
                self.launch()
            else:
                self.quit_app.emit(0)

    def launch(self):
        # self.core = core
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)

        if not self.offline:
            self.image_info.setText(self.tr("Downloading Images"))
            self.image_thread = ImageThread(self.core, self)
            self.image_thread.download_progess.connect(self.update_image_progbar)
            self.image_thread.finished.connect(self.finish)
            self.image_thread.finished.connect(lambda: self.image_info.setText(self.tr("Ready")))
            self.image_thread.finished.connect(self.image_thread.quit)
            self.image_thread.finished.connect(self.image_thread.deleteLater)
            self.image_thread.start()
        else:
            self.finish()

    def update_image_progbar(self, i: int):
        self.image_prog_bar.setValue(i)

    def finish(self):
        self.image_info.setText(self.tr("Starting..."))
        self.image_prog_bar.setValue(100)
        self.start_app.emit(self.offline)

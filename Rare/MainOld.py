import logging
import sys

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QTabWidget, QMainWindow, QWidget, QApplication, QDialog, QLabel, QProgressBar, QVBoxLayout

from Rare.Dialogs import LoginDialog
from Rare.TabWidgets import Settings, GameListInstalled, BrowserTab, GameListUninstalled, UpdateList
from Rare.utils import legendaryUtils
from Rare.utils.RareUtils import download_images

logging.basicConfig(
    format='[%(name)s] %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("Rare")


class LaunchThread(QThread):
    download_progess = pyqtSignal(int)
    action = pyqtSignal(str)

    def __init__(self, parent=None):
        super(LaunchThread, self).__init__(parent)

    def run(self):
        self.action.emit("Login")
        self.action.emit("Downloading Images")
        download_images(self.download_progess)
        self.action.emit("finish")


class LaunchDialog(QDialog):
    def __init__(self):
        super(LaunchDialog, self).__init__()
        try:
            if legendaryUtils.core.login():
                self.title = QLabel("<h3>Launching Rare</h3>")
                self.thread = LaunchThread(self)
                self.thread.download_progess.connect(self.update_pb)
                self.thread.action.connect(self.info)
                self.info_pb = QProgressBar()
                self.info_pb.setMaximum(len(legendaryUtils.get_games()))
                self.info_text = QLabel("Logging in")
                self.layout = QVBoxLayout()

                self.layout.addWidget(self.title)
                self.layout.addWidget(self.info_pb)
                self.layout.addWidget(self.info_text)

                self.setLayout(self.layout)
                self.thread.start()
        except:
            logger.info("No login data found")
            dia = LoginDialog()
            code = dia.get_login()
            if code == 1:
                self.app.closeAllWindows()
                logger.info("Exit login")
                exit(0)
            elif code == 0:
                logger.info("Login successfully")

    def update_pb(self, i: int):
        self.info_pb.setValue(i)

    def info(self, text: str):
        if text == "finish":
            self.close()
        self.info_text.setText(text)


class Main():
    def __init__(self):
        self.app = QApplication(sys.argv)

        self.launch_dia = LaunchDialog()
        self.launch_dia.exec_()


        self.window = MainWindow()
        self.app.exec_()

    def start(self):
        pass


def main():
    Main()


if __name__ == '__main__':
    main()

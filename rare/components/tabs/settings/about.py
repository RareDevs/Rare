import webbrowser
from logging import getLogger

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget

from rare import __version__, code_name
from rare.ui.components.tabs.settings.about import Ui_About
from rare.utils.qt_requests import QtRequestManager

logger = getLogger("About")


def versiontuple(v):
    try:
        return tuple(map(int, (v.split("."))))
    except:
        return tuple((9, 9, 9))  # It is a beta version and newer


class About(QWidget, Ui_About):
    update_available = False
    update_available_ready = pyqtSignal()

    def __init__(self):
        super(About, self).__init__()
        self.setupUi(self)

        self.version.setText(f"{__version__}  {code_name}")

        self.update_label.setVisible(False)
        self.update_lbl.setVisible(False)
        self.open_browser.setVisible(False)

        self.manager = QtRequestManager("json")
        self.manager.get("https://api.github.com/repos/Dummerle/Rare/releases/latest", self.update_available_finished)

        self.open_browser.clicked.connect(
            lambda: webbrowser.open("https://github.com/Dummerle/Rare/releases/latest"))

    def update_available_finished(self, data: dict):
        if latest_tag := data.get("tag_name"):
            self.update_available = versiontuple(latest_tag) > versiontuple(__version__)
        else:
            self.update_available = False

        if self.update_available:
            logger.info(f"Update available: {__version__} -> {latest_tag}")
            self.update_lbl.setText(self.tr("Update available: ") + f"{__version__} -> {latest_tag}")
            self.update_label.setVisible(True)
            self.update_lbl.setVisible(True)
            self.open_browser.setVisible(True)
            self.update_available_ready.emit()

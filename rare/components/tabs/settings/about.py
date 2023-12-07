import webbrowser
from logging import getLogger

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import QWidget

from rare import __version__, __codename__
from rare.ui.components.tabs.settings.about import Ui_About
from rare.utils.qt_requests import QtRequestManager

logger = getLogger("About")


def versiontuple(v):
    try:
        return tuple(map(int, (v.split("."))))
    except Exception:
        return tuple((9, 9, 9))  # It is a beta version and newer


class About(QWidget, Ui_About):
    update_available_ready = pyqtSignal()

    def __init__(self, parent=None):
        super(About, self).__init__(parent=parent)
        self.setupUi(self)

        self.version.setText(f"{__version__}  {__codename__}")

        self.update_label.setEnabled(False)
        self.update_lbl.setEnabled(False)
        self.open_browser.setVisible(False)
        self.open_browser.setEnabled(False)

        self.manager = QtRequestManager("json")
        self.manager.get(
            "https://api.github.com/repos/RareDevs/Rare/releases/latest",
            self.update_available_finished,
        )

        self.open_browser.clicked.connect(
            lambda: webbrowser.open("https://github.com/RareDevs/Rare/releases/latest")
        )

        self.update_available = False

    def showEvent(self, a0: QShowEvent) -> None:
        if a0.spontaneous():
            return super().showEvent(a0)
        self.manager.get(
            "https://api.github.com/repos/RareDevs/Rare/releases/latest",
            self.update_available_finished,
        )
        super().showEvent(a0)

    def update_available_finished(self, data: dict):
        if latest_tag := data.get("tag_name"):
            self.update_available = versiontuple(latest_tag) > versiontuple(__version__)
        else:
            self.update_available = False

        if self.update_available:
            logger.info(f"Update available: {__version__} -> {latest_tag}")
            self.update_lbl.setText("{} -> {}".format(__version__, latest_tag))
            self.update_available_ready.emit()
        else:
            self.update_lbl.setText(self.tr("You have the latest version"))
        self.update_label.setEnabled(self.update_available)
        self.update_lbl.setEnabled(self.update_available)
        self.open_browser.setVisible(self.update_available)
        self.open_browser.setEnabled(self.update_available)

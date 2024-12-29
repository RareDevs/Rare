import webbrowser
from logging import getLogger
from typing import Tuple

from PySide6.QtCore import Signal
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QWidget

from rare import __version__, __codename__
from rare.ui.components.tabs.settings.about import Ui_About
from rare.utils.qt_requests import QtRequests

logger = getLogger("About")


def versiontuple(v) -> Tuple[int, ...]:
    try:
        return tuple(map(int, (v.split("."))))
    except Exception as e:
        logger.error("Error while parsing version %s", v)
        logger.error(e)
        return 99, 99, 99, 999


class About(QWidget):
    update_available_ready = Signal()

    def __init__(self, parent=None):
        super(About, self).__init__(parent=parent)
        self.ui = Ui_About()
        self.ui.setupUi(self)

        self.ui.version.setText(f"{__version__}  {__codename__}")

        self.ui.update_label.setEnabled(False)
        self.ui.update_lbl.setEnabled(False)
        self.ui.open_browser.setVisible(False)
        self.ui.open_browser.setEnabled(False)

        self.releases_url = "https://api.github.com/repos/RareDevs/Rare/releases/latest"

        self.manager = QtRequests(parent=self)
        self.manager.get(self.releases_url, self.update_available_finished)

        self.ui.open_browser.clicked.connect(
            lambda: webbrowser.open("https://github.com/RareDevs/Rare/releases/latest")
        )

        self.update_available = False

    def showEvent(self, a0: QShowEvent) -> None:
        if a0.spontaneous():
            return super().showEvent(a0)
        self.manager.get(self.releases_url, self.update_available_finished)
        super().showEvent(a0)

    def update_available_finished(self, data: dict):
        if latest_tag := data.get("tag_name"):
            self.update_available = versiontuple(latest_tag) > versiontuple(__version__)
        else:
            self.update_available = False

        if self.update_available:
            logger.info(f"Update available: {__version__} -> {latest_tag}")
            self.ui.update_lbl.setText(f"{__version__} -> {latest_tag}")
            self.update_available_ready.emit()
        else:
            self.ui.update_lbl.setText(self.tr("You have the latest version"))
        self.ui.update_label.setEnabled(self.update_available)
        self.ui.update_lbl.setEnabled(self.update_available)
        self.ui.open_browser.setVisible(self.update_available)
        self.ui.open_browser.setEnabled(self.update_available)

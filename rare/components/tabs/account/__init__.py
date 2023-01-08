import webbrowser

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QLabel, QPushButton

from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton
from rare.utils.misc import icon


class AccountWidget(QWidget):
    logout: pyqtSignal = pyqtSignal()

    def __init__(self, parent):
        super(AccountWidget, self).__init__(parent=parent)
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()

        username = self.core.lgd.userdata.get("displayName")
        if not username:
            username = "Offline"

        self.open_browser = QPushButton(icon("fa.external-link"), self.tr("Account settings"))
        self.open_browser.clicked.connect(
            lambda: webbrowser.open(
                "https://www.epicgames.com/account/personal?productName=epicgames"
            )
        )
        self.logout_button = QPushButton(self.tr("Logout"))
        self.logout_button.clicked.connect(self.logout)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.tr("Account")))
        layout.addWidget(QLabel(self.tr("Logged in as <b>{}</b>").format(username)))
        layout.addWidget(self.open_browser)
        layout.addWidget(self.logout_button)

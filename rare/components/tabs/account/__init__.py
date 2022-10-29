import webbrowser

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QLabel, QPushButton

from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton
from rare.utils.misc import icon


class AccountWidget(QWidget):
    # int: exit code
    exit_app: pyqtSignal = pyqtSignal(int)
    logout = pyqtSignal()

    def __init__(self, parent):
        super(AccountWidget, self).__init__(parent=parent)
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()
        # FIXME: This is why widgets should be decoupled from procedures.
        # FIXME: pass downloads tab as argument to check if there are active downloads

        username = self.core.lgd.userdata.get("display_name")
        if not username:
            username = "Offline"

        self.open_browser = QPushButton(icon("fa.external-link"), self.tr("Account settings"))
        self.open_browser.clicked.connect(
            lambda: webbrowser.open(
                "https://www.epicgames.com/account/personal?productName=epicgames"
            )
        )
        self.logout_button = QPushButton(self.tr("Logout"))
        self.logout_button.clicked.connect(lambda: self.logout.emit())

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.tr("Account")))
        layout.addWidget(QLabel(self.tr("Logged in as <b>{}</b>").format(username)))
        layout.addWidget(self.open_browser)
        layout.addWidget(self.logout_button)

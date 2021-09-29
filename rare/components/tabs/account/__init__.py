import webbrowser

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QLabel, QPushButton

from legendary.core import LegendaryCore
from rare.utils.models import Signals


class MiniWidget(QWidget):
    def __init__(self, core: LegendaryCore, signals: Signals):
        super(MiniWidget, self).__init__()
        self.layout = QVBoxLayout()
        self.core = core
        self.signals = signals
        self.layout.addWidget(QLabel("Account"))
        username = self.core.lgd.userdata.get("display_name")
        if not username:
            try:
                self.core.login()
                username = self.core.lgd.userdata.get("display_name")
            except Exception:
                username = "Offline"

        self.layout.addWidget(QLabel(self.tr("Logged in as ") + str(username)))

        self.open_browser = QPushButton(self.tr("Account settings"))
        self.open_browser.clicked.connect(
            lambda: webbrowser.open("https://www.epicgames.com/account/personal?productName=epicgames"))
        self.layout.addWidget(self.open_browser)

        self.logout_button = QPushButton(self.tr("Logout"))
        self.logout_button.clicked.connect(self.logout)
        self.layout.addWidget(self.logout_button)
        self.setLayout(self.layout)

    def logout(self):
        reply = QMessageBox.question(self.parent().parent(), 'Message',
                                     self.tr("Do you really want to logout"), QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.core.lgd.invalidate_userdata()
            self.signals.app.emit((self.signals.actions.quit_app, -133742))  # restart exit code

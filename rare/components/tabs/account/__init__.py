import webbrowser

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QLabel, QPushButton

from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton
from rare.utils.misc import icon


class AccountWidget(QWidget):
    def __init__(self):
        super(AccountWidget, self).__init__()
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()

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
        self.logout_button.clicked.connect(self.logout)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.tr("Account")))
        layout.addWidget(QLabel(self.tr("Logged in as <b>{}</b>").format(username)))
        layout.addWidget(self.open_browser)
        layout.addWidget(self.logout_button)

    def logout(self):
        reply = QMessageBox.question(
            self.parent().parent(),
            "Message",
            self.tr("Do you really want to logout"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.core.lgd.invalidate_userdata()
            self.signals.exit_app.emit(-133742)  # restart exit code

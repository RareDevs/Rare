import webbrowser

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QLabel, QPushButton
from custom_legendary.core import LegendaryCore


class MiniWidget(QWidget):
    def __init__(self, core: LegendaryCore):
        super(MiniWidget, self).__init__()
        self.layout = QVBoxLayout()
        self.core = core
        self.layout.addWidget(QLabel("Account"))
        username = str(self.core.lgd.userdata.get("display_name"))
        if not username:
            self.core.login()
            username = str(self.core.lgd.userdata.get("display_name"))

        self.layout.addWidget(QLabel(self.tr("Logged in as ") + username))

        self.open_browser = QPushButton(self.tr("Account settings"))
        self.open_browser.clicked.connect(self.open_account)
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
            QCoreApplication.exit()

    def open_account(self):
        webbrowser.open("https://www.epicgames.com/account/personal?productName=epicgames")

import webbrowser

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QLabel, QPushButton
from legendary.core import LegendaryCore


class MiniWidget(QWidget):
    def __init__(self, core: LegendaryCore):
        super(MiniWidget, self).__init__()
        self.layout = QVBoxLayout()
        self.core = core
        self.layout.addWidget(QLabel("Account"))
        self.layout.addWidget(QLabel("Logged in as "+ self.core.lgd.userdata["display_name"]))

        self.open_browser = QPushButton("Account settings")
        self.open_browser.clicked.connect(self.open_account)
        self.layout.addWidget(self.open_browser)

        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.logout)
        self.layout.addWidget(self.logout_button)
        self.setLayout(self.layout)

    def logout(self):
        reply = QMessageBox.question(self.parent().parent(), 'Message',
                                     "Do you really want to logout", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.core.lgd.invalidate_userdata()
            QCoreApplication.exit(0)
            # self.core.lgd.invalidate_userdata()
        # exit()

    def open_account(self):
        webbrowser.open("https://www.epicgames.com/account/personal?productName=epicgames")
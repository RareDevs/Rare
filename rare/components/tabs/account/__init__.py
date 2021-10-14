import webbrowser

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QLabel, QPushButton

from rare import shared


class MiniWidget(QWidget):
    def __init__(self):
        super(MiniWidget, self).__init__()
        self.layout = QVBoxLayout()
        self.core = shared.core
        self.signals = shared.signals
        self.layout.addWidget(QLabel("Account"))
        username = self.core.lgd.userdata.get("display_name")
        if not username:
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
            self.signals.exit_app.emit(-133742)  # restart exit code

import webbrowser

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QLabel, QPushButton

from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton
from rare.utils.misc import icon


class AccountWidget(QWidget):
    # int: exit code
    exit_app: pyqtSignal = pyqtSignal(int)

    def __init__(self, parent, downloads_tab):
        super(AccountWidget, self).__init__(parent=parent)
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()
        # FIXME: This is why widgets should be decoupled from procedures.
        # FIXME: pass downloads tab as argument to check if there are active downloads
        self.downloads_tab = downloads_tab

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
        # FIXME: Don't allow logging out if there are active downloads
        if self.downloads_tab.is_download_active:
            warning = QMessageBox.warning(
                self,
                self.tr("Logout"),
                self.tr("There are active downloads. Stop them before logging out."),
                buttons=(QMessageBox.Ok),
                defaultButton=QMessageBox.Ok
            )
            return
        # FIXME: End of FIXME
        reply = QMessageBox.question(
            self,
            self.tr("Logout"),
            self.tr("Do you really want to logout <b>{}</b>?").format(self.core.lgd.userdata.get("display_name")),
            buttons=(QMessageBox.Yes | QMessageBox.No),
            defaultButton=QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.core.lgd.invalidate_userdata()
            self.exit_app.emit(-133742)  # restart exit code

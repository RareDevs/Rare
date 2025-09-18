import webbrowser

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from rare.lgndr.core import LegendaryCore
from rare.models.signals import GlobalSignals
from rare.utils.misc import ExitCodes, qta_icon


class AccountWidget(QWidget):
    exit_app: Signal = Signal(int)
    logout: Signal = Signal()

    def __init__(self, signals: GlobalSignals, core: LegendaryCore, parent):
        super(AccountWidget, self).__init__(parent=parent)
        self.signals = signals
        self.core = core

        username = self.core.lgd.userdata.get("displayName")
        if not username:
            username = "Offline"

        self.open_browser = QPushButton(
            qta_icon("fa.external-link", "fa5s.external-link-alt"),
            self.tr("Account settings"),
        )
        self.open_browser.clicked.connect(
            lambda: webbrowser.open("https://www.epicgames.com/account/personal?productName=epicgames")
        )
        self.logout_button = QPushButton(self.tr("Logout"), parent=self)
        self.logout_button.clicked.connect(self.__on_logout)
        self.quit_button = QPushButton(self.tr("Quit"), parent=self)
        self.quit_button.clicked.connect(self.__on_quit)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.tr("Account")))
        layout.addWidget(QLabel(self.tr("Logged in as <b>{}</b>").format(username)))
        layout.addWidget(self.open_browser)
        layout.addWidget(self.logout_button)
        layout.addWidget(self.quit_button)

    @Slot()
    def __on_quit(self):
        self.exit_app.emit(ExitCodes.EXIT)

    @Slot()
    def __on_logout(self):
        self.exit_app.emit(ExitCodes.LOGOUT)

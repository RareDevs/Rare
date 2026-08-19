import webbrowser

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QLabel, QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget

from rare.lgndr.core import LegendaryCore
from rare.models.signals import GlobalSignals
from rare.utils.misc import ExitCodes, qta_icon


class AccountWidget(QWidget):
    # int: exit code
    exit_app: Signal = Signal(int)
    logout: Signal = Signal()

    def __init__(self, signals: GlobalSignals, core: LegendaryCore, parent: QWidget | None = None):
        super(AccountWidget, self).__init__(parent=parent)
        self.signals = signals
        self.core = core

        username = self.core.lgd.userdata.get('displayName')
        if not username:
            username = 'Offline'

        self.open_browser = QPushButton(
            qta_icon('fa.external-link', 'fa5s.external-link-alt'),
            self.tr('Account settings'),
        )
        self.open_browser.clicked.connect(self._on_browser_clicked)

        self.logout_button = QPushButton(self.tr('Logout'), parent=self)
        self.logout_button.clicked.connect(self._on_logout)
        self.quit_button = QPushButton(self.tr('Quit'), parent=self)
        self.quit_button.clicked.connect(self._on_quit)

        self.center_widget = QWidget(self)
        center_widget = QVBoxLayout(self.center_widget)
        center_widget.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)
        center_widget.addWidget(QLabel(self.tr('Logged in as <b>{}</b>').format(username)))
        center_widget.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed))
        center_widget.addWidget(self.open_browser)
        center_widget.addWidget(self.logout_button)
        center_widget.addWidget(self.quit_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.center_widget, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

    @Slot()
    def _on_browser_clicked(self):
        webbrowser.open('https://www.epicgames.com/account/personal?productName=epicgames')

    @Slot()
    def _on_quit(self):
        self.exit_app.emit(ExitCodes.EXIT)

    @Slot()
    def _on_logout(self):
        self.exit_app.emit(ExitCodes.LOGOUT)

from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import Signal, Slot
from rare.lgndr.core import LegendaryCore
from rare.models.settings import RareAppSettings
from rare.components.dialogs.login.browser_login import BrowserLogin
from rare.components.dialogs.login.import_login import ImportLogin

class LoginPage(QWidget):
    success = Signal()

    def __init__(self, settings: RareAppSettings, rcore, parent=None):
        super().__init__(parent=parent)
        self.settings = settings
        self.rcore = rcore
        self.core: LegendaryCore = rcore.core()

        self.main_layout = QVBoxLayout(self)
        self.stacked_widget = QStackedWidget(self)
        self.main_layout.addWidget(self.stacked_widget)

        # Browser Login Widget
        self.browser_login_widget = BrowserLogin(self.core, self)
        self.browser_login_widget.success.connect(self.success.emit)
        self.stacked_widget.addWidget(self.browser_login_widget)

        # Import Login Widget
        self.import_login_widget = ImportLogin(self.core, self)
        self.import_login_widget.success.connect(self.success.emit)
        self.stacked_widget.addWidget(self.import_login_widget)

        # Navigation Buttons
        self.nav_buttons_layout = QHBoxLayout()
        self.browser_login_button = QPushButton("Login with Browser", self)
        self.browser_login_button.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.browser_login_widget))
        self.nav_buttons_layout.addWidget(self.browser_login_button)

        self.import_login_button = QPushButton("Import Login", self)
        self.import_login_button.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.import_login_widget))
        self.nav_buttons_layout.addWidget(self.import_login_button)
        
        self.main_layout.addLayout(self.nav_buttons_layout)

        # Set initial view
        self.stacked_widget.setCurrentWidget(self.browser_login_widget)

    @Slot()
    def do_login(self):
        current_widget = self.stacked_widget.currentWidget()
        if hasattr(current_widget, 'do_login'):
            current_widget.do_login()

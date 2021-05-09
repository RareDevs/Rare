from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QStackedLayout, QWidget, QPushButton

from custom_legendary.core import LegendaryCore
# Login Opportunities: Browser, Import
from rare.components.dialogs.login.browser_login import BrowserLogin
from rare.components.dialogs.login.import_widget import ImportWidget


class LoginDialog(QDialog):
    logged_in: bool = False

    def __init__(self, core: LegendaryCore):
        super(LoginDialog, self).__init__()

        self.core = core
        self.setWindowTitle("Rare - Login")
        self.setFixedWidth(350)
        self.setFixedHeight(450)

        self.init_ui()

    def init_ui(self):
        self.layout = QStackedLayout()

        self.landing_widget = QWidget()
        self.landing_layout = QVBoxLayout()

        self.title = QLabel(f"<h1>{self.tr('Welcome to Rare')}</h1>")
        self.landing_layout.addWidget(self.title)
        self.info_text = QLabel(self.tr("Select one option to Login"))
        self.landing_layout.addWidget(self.info_text)

        self.browser_login = OptionWidget(self.tr("Use Browser"),
                                          self.tr("This opens your default browser. Login and copy the text"))

        self.landing_layout.addWidget(self.browser_login)
        self.browser_login.button.clicked.connect(lambda: self.layout.setCurrentIndex(1))

        self.import_login = OptionWidget("Import from existing installation",
                                         "Import an existing login session from an Epic Games Launcher installation. You will get logged out there")
        self.import_login.button.clicked.connect(lambda: self.layout.setCurrentIndex(2))
        self.landing_layout.addWidget(self.import_login)

        self.close_button = QPushButton("Exit App")
        self.close_button.clicked.connect(self.close)
        self.landing_layout.addWidget(self.close_button)

        self.landing_widget.setLayout(self.landing_layout)
        self.layout.addWidget(self.landing_widget)

        self.browser_widget = BrowserLogin(self.core)
        self.browser_widget.success.connect(self.success)
        self.browser_widget.back.clicked.connect(lambda: self.layout.setCurrentIndex(0))
        self.layout.addWidget(self.browser_widget)

        self.import_widget = ImportWidget(self.core)
        self.import_widget.back.clicked.connect(lambda: self.layout.setCurrentIndex(0))
        self.import_widget.success.connect(self.success)
        self.layout.addWidget(self.import_widget)

        self.layout.addWidget(LoginSuccessfulWidget())

        self.setLayout(self.layout)

    def login(self):
        self.exec_()
        return self.logged_in

    def success(self):
        if self.core.login():
            self.logged_in = True
            self.layout.setCurrentIndex(3)
            # time.sleep(1)
        self.close()


class OptionWidget(QWidget):
    def __init__(self, btn_text: str, info_text: str):
        super(OptionWidget, self).__init__()
        self.layout = QVBoxLayout()
        self.text = QLabel(info_text)
        self.text.setWordWrap(True)
        self.button = QPushButton(btn_text)

        self.layout.addWidget(self.button)
        self.layout.addWidget(self.text)

        self.setLayout(self.layout)


class LoginSuccessfulWidget(QWidget):
    def __init__(self):
        super(LoginSuccessfulWidget, self).__init__()
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("Login Successful"))
        self.setLayout(self.layout)

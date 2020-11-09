import os

from PyQt5.QtWidgets import QDialog, QStackedLayout, QHBoxLayout, QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel

from Rare.Login import ImportWidget, LoginWidget


class LoginDialog(QDialog):

    def __init__(self):
        self.code = 1
        super(LoginDialog, self).__init__()
        self.layout = QStackedLayout()

        self.widget = QWidget()
        self.import_widget = ImportWidget()
        self.login_widget = LoginWidget()
        self.login_widget.signal.connect(self.login_success)
        self.import_widget.signal.connect(self.login_success)

        self.initWidget()

        self.layout.insertWidget(0, self.widget)
        self.layout.insertWidget(1, self.login_widget)
        self.layout.insertWidget(2, self.import_widget)

        self.setLayout(self.layout)
        self.layout.setCurrentIndex(0)
        self.show()

    def initWidget(self):
        self.widget_layout = QVBoxLayout()
        self.login_button = QPushButton("Login via Browser")
        self.import_button = QPushButton("Import from existing EGL installation")
        self.close_button = QPushButton("Exit")

        # self.login_button.clicked.connect(self.login)
        self.import_button.clicked.connect(self.set_import_widget)
        self.login_button.clicked.connect(self.set_login_widget)
        self.close_button.clicked.connect(self.exit_login)

        self.widget_layout.addWidget(self.login_button)
        self.widget_layout.addWidget(self.import_button)
        self.widget_layout.addWidget(self.close_button)
        self.widget.setLayout(self.widget_layout)

    def login_success(self):
        self.code = 0
        self.close()

    def get_login(self):
        self.exec_()
        return self.code

    def set_login_widget(self):
        self.layout.setCurrentIndex(1)

    def set_import_widget(self):
        self.layout.setCurrentIndex(2)

    def exit_login(self):
        self.code = 1
        self.close()


class InstallDialog(QDialog):
    def __init__(self, game):
        super(InstallDialog, self).__init__()
        self.setWindowTitle("Install Game")
        self.layout = QVBoxLayout()
        self.yes = False
        self.install_path = QLineEdit(f"{os.path.expanduser('~')}/legendary")
        self.options = QLabel("Verschiedene Optionene")
        self.layout.addWidget(self.options)

        self.layout.addStretch(1)
        self.yes_button = QPushButton("Install")
        self.yes_button.clicked.connect(self.close)
        self.cancel_button = QPushButton("cancel")

        self.layout.addWidget(self.options)
        self.layout.addWidget(self.install_path)

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.yes_button)
        self.button_layout.addWidget(self.cancel_button)
        self.yes_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.cancel)
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)

    def get_data(self) -> dict:
        self.exec_()
        return {
            "install_path": self.install_path.text()
        } if self.yes else 0

    def accept(self):
        self.yes = True
        self.close()

    def cancel(self):
        self.yes = False
        self.close()


class GameSettingsDialog(QDialog):
    action: str = None

    def __init__(self, settings=None):
        super(GameSettingsDialog, self).__init__()
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("Einstellungen"))

        self.wine_prefix_text = QLabel("Wine prefix")
        self.wine_prefix = QLineEdit(f"{os.path.expanduser('~')}/.wine")
        self.wine_prefix.setPlaceholderText("Wineprefix")
        self.uninstall_button = QPushButton("Uninstall Game")
        self.uninstall_button.clicked.connect(self.uninstall)
        self.save_button = QPushButton("Save settings")
        self.exit_button = QPushButton("Exit withot save")
        self.exit_button.clicked.connect(self.close)
        self.save_button.clicked.connect(self.exit_settings)

        self.layout.addWidget(self.wine_prefix_text)
        self.layout.addWidget(self.wine_prefix)
        self.layout.addWidget(self.uninstall_button)
        self.layout.addWidget(self.save_button)
        self.layout.addWidget(self.exit_button)

        self.setLayout(self.layout)

    def get_settings(self):
        self.exec_()
        return self.action

    def uninstall(self):
        self.action = "uninstall"
        self.close()

    def exit_settings(self):
        self.action = self.wine_prefix.text()
        self.close()

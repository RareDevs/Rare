import json
import os
import webbrowser
from getpass import getuser
from json import loads
from logging import getLogger

from PyQt5.QtCore import QUrl, pyqtSignal
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtWidgets import QDialog, QWidget, QVBoxLayout, QLabel, QPushButton, QStackedLayout, QLineEdit, QButtonGroup, \
    QRadioButton
from legendary.core import LegendaryCore

logger = getLogger("LoginWindow")


class LoginBrowser(QWebEngineView):
    def __init__(self):
        super(LoginBrowser, self).__init__()
        self.browser_profile = QWebEngineProfile("storage", self)
        self.webpage = QWebEnginePage(self.browser_profile, self)
        self.setPage(self.webpage)

    def createWindow(self, webengine_window_type):
        return self


class ImportWidget(QWidget):
    signal = pyqtSignal(bool)

    def __init__(self, core: LegendaryCore):

        super(ImportWidget, self).__init__()
        self.wine_paths = []
        self.layout = QVBoxLayout()
        self.core = core

        self.import_text = QLabel("<h2>Import from existing Epic Games Launcher installation</h2>\nYou will get "
                                  "logged out there")
        self.import_accept_button = QPushButton("Import")
        self.import_accept_button.clicked.connect(self.auth)
        appdata_paths = self.get_appdata_path()

        self.layout.addWidget(self.import_text)

        if len(appdata_paths) == 0:
            self.path = QLineEdit()
            self.path.setPlaceholderText("Path to Wineprefix (Not implemented)")
            self.layout.addWidget(self.path)
        else:
            self.btn_group = QButtonGroup()
        for i in appdata_paths:
            radio_button = QRadioButton(i)
            self.btn_group.addButton(radio_button)
            self.layout.addWidget(radio_button)

        # for i in appdata_paths:

        self.appdata_path_text = QLabel(f"Appdata path: {self.core.egl.appdata_path}")

        self.login_text = QLabel("")
        # self.layout.addWidget(self.btn_group)
        self.layout.addWidget(self.login_text)
        self.layout.addStretch(1)
        self.layout.addWidget(self.import_accept_button)

        self.setLayout(self.layout)

    def get_appdata_path(self) -> list:
        if self.core.egl.appdata_path:
            return [self.core.egl.appdata_path]

        else:  # Linux
            wine_paths = []
            possible_wine_paths = [os.path.expanduser('~/Games/epic-games-store/'),
                                   os.path.expanduser('~/.wine/')]

            for i in possible_wine_paths:
                if os.path.exists(i):
                    if os.path.exists(os.path.join(i, "drive_c/users", getuser(),
                                                   'Local Settings/Application Data/EpicGamesLauncher',
                                                   'Saved/Config/Windows')):
                        wine_paths.append(i)

            if len(wine_paths) > 0:
                appdata_dirs = [
                    os.path.join(i, "drive_c/users", getuser(), 'Local Settings/Application Data/EpicGamesLauncher',
                                 'Saved/Config/Windows') for i in wine_paths]
                return appdata_dirs
        return []

    def auth(self):
        self.import_accept_button.setDisabled(True)
        if not self.btn_group:
            self.core.egl.appdata_path = self.path.text()

        for i in self.btn_group.buttons():

            if i.isChecked():
                self.core.egl.appdata_path = i.text()
        try:
            if self.core.auth_import():
                logger.info(f"Logged in as {self.core.lgd.userdata['displayName']}")
                self.signal.emit(True)
                return

        except:
            pass

        self.import_accept_button.setDisabled(False)
        logger.warning("Error: No valid session found")
        self.login_text.setText("Error: No valid session found")


class SystemBrowserWidget(QWidget):
    signal = pyqtSignal(bool)

    def __init__(self, core: LegendaryCore):
        super(SystemBrowserWidget, self).__init__()
        self.core = core
        self.layout = QVBoxLayout()

        self.text = QLabel("Insert Sid from Browser")
        self.layout.addWidget(self.text)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Insert sid from Browser")
        self.layout.addWidget(self.input)

        self.loading_text = QLabel("")
        self.layout.addWidget(self.loading_text)

        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.back)
        self.layout.addWidget(self.back_button)

        self.submit_button = QPushButton("Login")
        self.submit_button.clicked.connect(self.login)
        self.layout.addWidget(self.submit_button)

        self.setLayout(self.layout)

    def login(self):
        self.loading_text.setText("Loading")
        token = self.input.text()
        if token.startswith("{") and token.endswith("}"):
            token = json.loads(token)['sid']
        token = self.core.auth_sid(token)
        if self.core.auth_code(token):
            logger.info("Successfully logged in")
            self.signal.emit(True)
        else:
            logger.warning("Login failed")
            self.loading_text.setText("Login failed")

    def back(self):
        self.signal.emit(False)


class LoginWindow(QDialog):
    signal = pyqtSignal(bool)

    def __init__(self, core: LegendaryCore):
        super(LoginWindow, self).__init__()
        self.core = core
        self.success_code = False
        self.widget = QWidget()
        self.setGeometry(0, 0, 200, 300)
        self.welcome_layout = QVBoxLayout()
        self.title = QLabel(
            "<h2>Welcome to Rare the graphical interface for Legendary, an open source Epic Games alternative.</h2>\n<h3>Select one Option to Login</h3>")
        self.browser_btn = QPushButton("Use built in browser to login")
        self.browser_btn.clicked.connect(self.browser_login)
        self.browser_btn_normal = QPushButton("Use System browser")
        self.browser_btn_normal.clicked.connect(self.sys_browser_login)
        self.import_btn = QPushButton("Import from existing Epic Games installation")

        self.import_btn.clicked.connect(self.import_login)
        self.text = QLabel("")
        self.exit_btn = QPushButton("Exit App")
        self.exit_btn.clicked.connect(self.exit_login)

        self.welcome_layout.addWidget(self.title)
        self.welcome_layout.addWidget(self.browser_btn)
        self.welcome_layout.addWidget(self.browser_btn_normal)
        self.welcome_layout.addWidget(self.import_btn)
        self.welcome_layout.addWidget(self.text)
        self.welcome_layout.addWidget(self.exit_btn)
        self.widget.setLayout(self.welcome_layout)

        self.browser = LoginBrowser()
        self.browser.loadFinished.connect(self.check_for_sid_page)

        self.import_widget = ImportWidget(self.core)
        self.import_widget.signal.connect(self.login_signal)

        self.sys_browser_widget = SystemBrowserWidget(core)
        self.sys_browser_widget.signal.connect(self.login_signal)

        self.layout = QStackedLayout()
        self.layout.addWidget(self.widget)
        self.layout.addWidget(self.browser)
        self.layout.addWidget(self.import_widget)
        self.layout.addWidget(self.sys_browser_widget)
        self.setLayout(self.layout)
        self.show()

    def login_signal(self, b: bool):
        if b:
            self.success()
        else:
            self.layout.setCurrentIndex(0)
            self.text.setText("<h4 style='color: red'>Login failed</h4>")

    def login(self):
        self.exec_()
        return self.success_code

    def success(self):
        self.success_code = True
        self.close()

    def retry(self):
        self.__init__(self.core)

    def exit_login(self):
        self.code = 1
        self.close()

    def browser_login(self):
        self.setGeometry(0, 0, 800, 600)
        self.browser.load(QUrl(
            'https://www.epicgames.com/id/login?redirectUrl=https%3A%2F%2Fwww.epicgames.com%2Fid%2Fapi%2Fredirect'))
        self.layout.setCurrentIndex(1)

    def sys_browser_login(self):
        self.layout.setCurrentIndex(3)
        webbrowser.open(
            "https://www.epicgames.com/id/login?redirectUrl=https%3A%2F%2Fwww.epicgames.com%2Fid%2Fapi%2Fredirect")

    def import_login(self):
        self.layout.setCurrentIndex(2)

    def check_for_sid_page(self):
        if self.browser.url() == QUrl("https://www.epicgames.com/id/api/redirect"):
            self.browser.page().toPlainText(self.browser_auth)

    def browser_auth(self, json):
        token = self.core.auth_sid(loads(json)["sid"])
        if self.core.auth_code(token):
            logger.info(f"Successfully logged in as {self.core.lgd.userdata['displayName']}")
            self.success()
        else:
            self.layout.setCurrentIndex(0)
            logger.warning("Login failed")
            self.browser.close()
            self.text.setText("Login Failed")

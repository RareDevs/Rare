import os
from getpass import getuser
from json import loads
from logging import getLogger

from PyQt5.QtCore import QUrl, pyqtSignal
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QDialog, QWidget, QVBoxLayout, QLabel, QPushButton, QStackedLayout
from legendary.core import LegendaryCore

logger = getLogger("LoginWindow")


class LoginBrowser(QWebEngineView):
    def __init__(self):
        super(LoginBrowser, self).__init__()

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
        self.set_appdata_path()
        self.appdata_path_text = QLabel(f"Appdata path: {self.core.egl.appdata_path}")

        self.layout.addWidget(self.import_text)
        self.layout.addWidget(self.appdata_path_text)
        self.layout.addStretch(1)
        self.layout.addWidget(self.import_accept_button)

        self.setLayout(self.layout)

    def set_appdata_path(self):
        if self.core.egl.appdata_path:
            self.wine_paths.append(self.core.egl.appdata_path)

        else:  # Linux
            wine_paths = []
            if os.path.exists(os.path.expanduser('~/Games/epic-games-store/drive_c/users')):
                wine_paths.append(os.path.expanduser('~/Games/epic-games-store/drive_c/users'))
            if os.path.exists(os.path.expanduser('~/.wine/drive_c/users')):
                wine_paths.append(os.path.expanduser('~/.wine/drive_c/users'))
            appdata_dirs = [os.path.join(i, getuser(),
                                         'Local Settings/Application Data/EpicGamesLauncher',
                                         'Saved/Config/Windows') for i in wine_paths]
            if appdata_dirs == 0:
                return
            for i in appdata_dirs:
                if os.path.exists(i):
                    self.wine_paths.append(i)
            self.core.egl.appdata_path = wine_paths[0]

    def auth(self):
        self.import_accept_button.setDisabled(True)
        for i, path in enumerate(self.wine_paths):
            self.appdata_path_text.setText(f"Appdata path: {self.core.egl.appdata_path}")
            self.core.egl.appdata_path = path
            try:
                if self.core.auth_import():
                    logger.info(f"Logged in as {self.core.lgd.userdata['displayName']}")
                    self.signal.emit(True)
                    return
                else:
                    logger.warning("Error: No valid session found")
            except:
                logger.warning("Error: No valid session found")

        self.signal.emit(False)


class LoginWindow(QDialog):
    def __init__(self, core: LegendaryCore):
        super(LoginWindow, self).__init__()
        self.core = core
        self.success_code = False
        self.widget = QWidget()
        self.setGeometry(0, 0, 200, 300)
        self.welcome_layout = QVBoxLayout()
        self.title = QLabel(
            "<h2>Welcome to Rare the graphical interface for Legendary, an open source Epic Games alternative.</h2>\n<h3>Select one Option to Login</h3>")
        self.browser_btn = QPushButton("Use browser to login")
        self.browser_btn.clicked.connect(self.browser_login)
        self.import_btn = QPushButton("Import from existing Epic Games installation")

        self.import_btn.clicked.connect(self.import_login)
        self.text = QLabel("")
        self.exit_btn = QPushButton("Exit App")
        self.exit_btn.clicked.connect(self.exit_login)

        self.welcome_layout.addWidget(self.title)
        self.welcome_layout.addWidget(self.browser_btn)
        self.welcome_layout.addWidget(self.import_btn)
        self.welcome_layout.addWidget(self.text)
        self.welcome_layout.addWidget(self.exit_btn)
        self.widget.setLayout(self.welcome_layout)

        self.browser = LoginBrowser()
        self.browser.loadFinished.connect(self.check_for_sid_page)

        self.import_widget = ImportWidget(self.core)
        self.import_widget.signal.connect(self.import_resp)
        self.layout = QStackedLayout()
        self.layout.addWidget(self.widget)
        self.layout.addWidget(self.browser)
        self.layout.addWidget(self.import_widget)
        self.setLayout(self.layout)
        self.show()

    def import_resp(self, b: bool):
        if b:
            self.success()
        else:
            self.layout.setCurrentIndex(0)
            self.text.setText("<h4 style='color: red'>No valid session found</h4>")

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

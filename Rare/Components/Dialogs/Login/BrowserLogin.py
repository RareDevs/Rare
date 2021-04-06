import json
from logging import getLogger

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit

from custom_legendary.core import LegendaryCore

logger = getLogger("BrowserLogin")


class BrowserLogin(QWidget):
    success = pyqtSignal()
    url: str = "https://www.epicgames.com/id/login?redirectUrl=https%3A%2F%2Fwww.epicgames.com%2Fid%2Fapi%2Fredirect"

    def __init__(self, core: LegendaryCore):
        super(BrowserLogin, self).__init__()
        self.layout = QVBoxLayout()
        self.core = core

        self.back = QPushButton("Back")  # TODO Icon
        self.layout.addWidget(self.back)

        self.info_text = QLabel(self.tr(
            "Opens a browser. You login and copy the json code in the field below. Click <a href='{}'>here</a> to open Browser").format(
            self.url))
        self.info_text.setWordWrap(True)
        self.info_text.setOpenExternalLinks(True)
        self.layout.addWidget(self.info_text)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(self.tr("Insert SID here"))
        self.layout.addWidget(self.input_field)

        self.mini_info = QLabel("")

        self.login_btn = QPushButton(self.tr("Login"))
        self.login_btn.clicked.connect(self.login)
        self.layout.addWidget(self.login_btn)

        self.setLayout(self.layout)

    def login(self):
        self.mini_info.setText(self.tr("Loading..."))
        sid = self.input_field.text()
        # when the text copied
        if sid.startswith("{") and sid.endswith("}"):
            sid = json.loads(sid)["sid"]
        token = self.core.auth_sid(sid)
        if self.core.auth_code(token):
            logger.info(f"Successfully logged in as {self.core.lgd.userdata['displayName']}")
            self.success.emit()
        else:
            self.mini_info.setText("Login failed")

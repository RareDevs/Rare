import json
from logging import getLogger

from PyQt5.QtCore import pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QWidget

from custom_legendary.core import LegendaryCore
from rare.ui.components.dialogs.login.browser_login import Ui_BrowserLogin

logger = getLogger("BrowserLogin")


class BrowserLogin(QWidget, Ui_BrowserLogin):
    success = pyqtSignal()
    changed = pyqtSignal()
    login_url = "https://www.epicgames.com/id/login?redirectUrl=https%3A%2F%2Fwww.epicgames.com%2Fid%2Fapi%2Fredirect"

    def __init__(self, core: LegendaryCore, parent=None):
        super(BrowserLogin, self).__init__(parent=parent)
        self.setupUi(self)

        self.core = core

        self.open_button.clicked.connect(self.open_browser)
        self.sid_edit.textChanged.connect(self.changed.emit)

    def is_valid(self):
        return len(self.sid_edit.text()) == 32

    def do_login(self):
        self.status_label.setText(self.tr("Logging in..."))
        sid = self.sid_edit.text()
        # when the text copied
        if sid.startswith("{") and sid.endswith("}"):
            sid = json.loads(sid)["sid"]
        try:
            token = self.core.auth_sid(sid)
            if self.core.auth_code(token):
                logger.info(f"Successfully logged in as {self.core.lgd.userdata['displayName']}")
                self.success.emit()
            else:
                self.status_label.setText(self.tr("Login failed."))
                logger.warning("Failed to login through browser")
        except Exception as e:
            logger.warning(e)

    def open_browser(self):
        QDesktopServices.openUrl(QUrl(self.login_url))

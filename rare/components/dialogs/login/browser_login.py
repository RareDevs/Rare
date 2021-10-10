import json
from logging import getLogger
from typing import Tuple

from PyQt5.QtCore import pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QWidget

from legendary.core import LegendaryCore
from rare.ui.components.dialogs.login.browser_login import Ui_BrowserLogin
from rare.utils.extra_widgets import IndicatorLineEdit

logger = getLogger("BrowserLogin")


class BrowserLogin(QWidget, Ui_BrowserLogin):
    success = pyqtSignal()
    changed = pyqtSignal()
    login_url = "https://www.epicgames.com/id/login?redirectUrl=https%3A%2F%2Fwww.epicgames.com%2Fid%2Fapi%2Fredirect"

    def __init__(self, core: LegendaryCore, parent=None):
        super(BrowserLogin, self).__init__(parent=parent)
        self.setupUi(self)

        self.core = core

        self.sid_edit = IndicatorLineEdit(
            ph_text=self.tr("Insert SID here"),
            edit_func=self.text_changed,
            parent=self
        )
        self.sid_layout.addWidget(self.sid_edit)

        self.open_button.clicked.connect(self.open_browser)
        self.sid_edit.textChanged.connect(self.changed.emit)

    def is_valid(self):
        return self.sid_edit.is_valid

    @staticmethod
    def text_changed(text) -> Tuple[bool, str]:
        if text:
            text = text.strip()
            if text.startswith("{") and text.endswith("}"):
                try:
                    text = json.loads(text).get("sid")
                except json.JSONDecodeError:
                    return False, text
            elif '"' in text:
                text = text.strip('"')
            return len(text) == 32, text
        else:
            return False, text

    def do_login(self):
        self.status_label.setText(self.tr("Logging in..."))
        sid = self.sid_edit.text()
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

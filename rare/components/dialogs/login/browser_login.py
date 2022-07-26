import json
from logging import getLogger
from typing import Tuple

from PyQt5.QtCore import pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QFrame, qApp
from legendary.core import LegendaryCore
from legendary.utils import webview_login

from rare.ui.components.dialogs.login.browser_login import Ui_BrowserLogin
from rare.utils.extra_widgets import IndicatorLineEdit
from rare.utils.misc import icon

logger = getLogger("BrowserLogin")


class BrowserLogin(QFrame):
    success = pyqtSignal()
    changed = pyqtSignal()
    login_url = (
        "https://www.epicgames.com/id/login?redirectUrl=https%3A%2F%2Fwww.epicgames.com%2Fid%2Fapi%2Fredirect"
    )

    def __init__(self, core: LegendaryCore, parent=None):
        super(BrowserLogin, self).__init__(parent=parent)
        self.setFrameStyle(self.StyledPanel)
        self.ui = Ui_BrowserLogin()
        self.ui.setupUi(self)

        self.core = core

        self.sid_edit = IndicatorLineEdit(
            placeholder=self.tr("Insert SID here"), edit_func=self.text_changed, parent=self
        )
        self.ui.link_text.setText(self.login_url)
        self.ui.copy_button.setIcon(icon("mdi.content-copy", "fa.copy"))
        self.ui.copy_button.clicked.connect(self.copy_link)

        self.ui.sid_layout.addWidget(self.sid_edit)

        self.ui.open_button.clicked.connect(self.open_browser)
        self.sid_edit.textChanged.connect(self.changed.emit)

    def copy_link(self):
        clipboard = qApp.clipboard()
        clipboard.setText(self.login_url)
        self.ui.status_label.setText(self.tr("Copied to clipboard"))

    def is_valid(self):
        return self.sid_edit.is_valid

    @staticmethod
    def text_changed(text) -> Tuple[bool, str, str]:
        if text:
            text = text.strip()
            if text.startswith("{") and text.endswith("}"):
                try:
                    text = json.loads(text).get("sid")
                except json.JSONDecodeError:
                    return False, text, IndicatorLineEdit.reasons.wrong_format
            elif '"' in text:
                text = text.strip('"')
            return len(text) == 32, text, IndicatorLineEdit.reasons.wrong_format
        else:
            return False, text, ""

    def do_login(self):
        self.ui.status_label.setText(self.tr("Logging in..."))
        sid = self.sid_edit.text()
        try:
            token = self.core.auth_sid(sid)
            if self.core.auth_code(token):
                logger.info(f"Successfully logged in as {self.core.lgd.userdata['displayName']}")
                self.success.emit()
            else:
                self.ui.status_label.setText(self.tr("Login failed."))
                logger.warning("Failed to login through browser")
        except Exception as e:
            logger.warning(e)

    def open_browser(self):
        if webview_login.webview_available is False:
            logger.warning("You don't have webengine installed, " "you will need to manually copy the SID.")
            QDesktopServices.openUrl(QUrl(self.login_url))
        else:
            if webview_login.do_webview_login(
                callback_sid=self.core.auth_sid, callback_code=self.core.auth_code
            ):
                logger.info("Successfully logged in as " f"{self.core.lgd.userdata['displayName']}")
                self.success.emit()
            else:
                logger.warning("Failed to login through browser.")

import json
from logging import getLogger
from typing import Tuple

from PySide6.QtCore import Signal, QUrl, QProcess, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFrame, QApplication, QFormLayout, QLineEdit
from legendary.utils import webview_login

from rare.lgndr.core import LegendaryCore
from rare.ui.components.dialogs.login.browser_login import Ui_BrowserLogin
from rare.utils.misc import qta_icon
from rare.utils.paths import get_rare_executable
from rare.widgets.indicator_edit import IndicatorLineEdit, IndicatorReasonsCommon

logger = getLogger("BrowserLogin")


class BrowserLogin(QFrame):
    success = Signal()
    isValid = Signal(bool)

    def __init__(self, core: LegendaryCore, parent=None):
        super(BrowserLogin, self).__init__(parent=parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.ui = Ui_BrowserLogin()
        self.ui.setupUi(self)

        self.core = core
        self.login_url = self.core.egs.get_auth_url()

        self.sid_edit = IndicatorLineEdit(
            placeholder=self.tr("Insert authorizationCode here"), edit_func=self.sid_edit_callback, parent=self
        )
        self.sid_edit.line_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.ui.link_text.setText(self.login_url)
        self.ui.copy_button.setIcon(qta_icon("mdi.content-copy", "fa.copy"))
        self.ui.copy_button.clicked.connect(self.copy_link)
        self.ui.form_layout.setWidget(
            self.ui.form_layout.getWidgetPosition(self.ui.sid_label)[0],
            QFormLayout.ItemRole.FieldRole, self.sid_edit
        )

        self.ui.open_button.clicked.connect(self.open_browser)
        self.sid_edit.textChanged.connect(lambda _: self.isValid.emit(self.is_valid()))

    @Slot()
    def copy_link(self):
        clipboard = QApplication.instance().clipboard()
        clipboard.setText(self.login_url)
        self.ui.status_label.setText(self.tr("Copied to clipboard"))

    def is_valid(self):
        return self.sid_edit.is_valid

    @staticmethod
    def sid_edit_callback(text) -> Tuple[bool, str, int]:
        if text:
            text = text.strip()
            if text.startswith("{") and text.endswith("}"):
                try:
                    text = json.loads(text).get("authorizationCode")
                except json.JSONDecodeError:
                    return False, text, IndicatorReasonsCommon.WRONG_FORMAT
            elif '"' in text:
                text = text.strip('"')
            return len(text) == 32, text, IndicatorReasonsCommon.WRONG_FORMAT
        else:
            return False, text, IndicatorReasonsCommon.VALID

    def do_login(self):
        self.ui.status_label.setText(self.tr("Logging in..."))
        auth_code = self.sid_edit.text()
        try:
            if self.core.auth_code(auth_code):
                logger.info("Successfully logged in as %s", self.core.lgd.userdata['displayName'])
                self.success.emit()
            else:
                self.ui.status_label.setText(self.tr("Login failed."))
                logger.warning("Failed to login through browser")
        except Exception as e:
            logger.warning(e)

    @Slot()
    def open_browser(self):
        if not webview_login.webview_available:
            logger.warning("You don't have webengine installed, you will need to manually copy the authorizationCode.")
            QDesktopServices.openUrl(QUrl(self.login_url))
        else:
            cmd = get_rare_executable() + ["login", self.core.get_egl_version()]
            proc = QProcess(self)
            proc.start(cmd[0], cmd[1:])
            proc.waitForFinished(-1)
            out, err = (
                proc.readAllStandardOutput().data().decode("utf-8", "ignore"),
                proc.readAllStandardError().data().decode("utf-8", "ignore")
            )
            proc.deleteLater()

            if out:
                self.core.auth_ex_token(out)
                logger.info("Successfully logged in as %s", {self.core.lgd.userdata['displayName']})
                self.success.emit()
            else:
                logger.warning("Failed to login through browser.")

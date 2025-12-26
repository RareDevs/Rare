from argparse import Namespace

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QFrame, QLayout, QMessageBox

from rare.lgndr.core import LegendaryCore
from rare.ui.components.dialogs.login.landing_page import Ui_LandingPage
from rare.ui.components.dialogs.login.login_dialog import Ui_LoginDialog
from rare.utils.misc import qta_icon
from rare.widgets.dialogs import BaseDialog
from rare.widgets.sliding_stack import SlidingStackedWidget

from .browser_login import BrowserLogin
from .import_login import ImportLogin


class LandingPage(QFrame):
    def __init__(self, parent=None):
        super(LandingPage, self).__init__(parent=parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.ui = Ui_LandingPage()
        self.ui.setupUi(self)


class LoginDialog(BaseDialog):
    def __init__(self, args: Namespace, core: LegendaryCore, parent=None):
        super(LoginDialog, self).__init__(parent=parent)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.MSWindowsFixedSizeDialogHint
        )

        self.ui = Ui_LoginDialog()
        self.ui.setupUi(self)

        self.logged_in: bool = False

        self.args = args
        self.core = core

        self.login_stack = SlidingStackedWidget(parent=self)
        self.ui.main_layout.insertWidget(3, self.login_stack, stretch=1)

        self.landing_page = LandingPage(self.login_stack)
        self.landing_index = self.login_stack.insertWidget(0, self.landing_page)

        self.browser_page = BrowserLogin(self.core, self.login_stack)
        self.browser_index = self.login_stack.insertWidget(1, self.browser_page)
        self.browser_page.success.connect(self._on_login_successful)
        self.browser_page.validated.connect(self._on_page_validated)
        self.import_page = ImportLogin(self.core, self.login_stack)
        self.import_index = self.login_stack.insertWidget(2, self.import_page)
        self.import_page.success.connect(self._on_login_successful)
        self.import_page.validated.connect(self._on_page_validated)

        self.info_message = {
            self.landing_index: self.tr(
                "<i>Select log-in method.</i>"
            ),
            self.browser_index: self.tr(
                "<i>Click the <strong>Open Browser</strong> button to open the "
                "login page in your web browser or copy the link and paste it "
                "in any web browser. After logging in using the browser, copy "
                "the text in the quotes after </i><code><b>authorizationCode</b></code><i> "
                "in the same line into the empty input above."
                "<br><br><strong>DO NOT SHARE THE INFORMATION IN THE BROWSER PAGE WITH "
                "ANYONE IN ANY FORM (TEXT OR SCREENSHOT)!</strong></i>"
            ),
            self.import_index: self.tr(
                "<i>Select the Wine prefix where Epic Games Launcher is installed. "
                "You will get logged out from EGL in the process.</i>"
            ),
        }
        self.ui.info_label.setText(self.info_message[self.landing_index])

        self.login_stack.setMinimumWidth(640)
        self.login_stack.setMinimumHeight(180)
        self.ui.info_label.setMinimumWidth(640)
        self.ui.info_label.setMinimumHeight(40)

        self.ui.next_button.setEnabled(False)
        self.ui.back_button.setEnabled(False)

        self.landing_page.ui.login_browser_radio.clicked.connect(self._on_radio_clicked)
        self.landing_page.ui.login_browser_radio.clicked.connect(self._on_browser_radio_clicked)
        self.landing_page.ui.login_import_radio.clicked.connect(self._on_radio_clicked)
        self.landing_page.ui.login_import_radio.clicked.connect(self._on_import_radio_clicked)

        self.ui.exit_button.clicked.connect(self.reject)
        self.ui.back_button.clicked.connect(self._on_back_clicked)
        self.ui.next_button.clicked.connect(self._on_next_clicked)

        self.login_stack.setCurrentWidget(self.landing_page)

        self.ui.exit_button.setIcon(qta_icon("fa.remove", "fa5s.times"))
        self.ui.back_button.setIcon(qta_icon("fa.chevron-left", "fa5s.chevron-left"))
        self.ui.next_button.setIcon(qta_icon("fa.chevron-right", "fa5s.chevron-right"))

        # lk: Set next as the default button only to stop closing the dialog when pressing enter
        self.ui.exit_button.setAutoDefault(False)
        self.ui.back_button.setAutoDefault(False)
        self.ui.next_button.setAutoDefault(True)

        self.ui.main_layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    @Slot()
    def _on_radio_clicked(self):
        self.ui.next_button.setEnabled(True)

    @Slot(bool)
    def _on_page_validated(self, valid: bool):
        self.ui.next_button.setEnabled(valid)

    @Slot()
    def _on_browser_radio_clicked(self):
        self.login_stack.slideInWidget(self.browser_page)
        self.ui.info_label.setText(self.info_message[self.browser_index])
        self.ui.back_button.setEnabled(True)
        self.ui.next_button.setEnabled(False)

    @Slot()
    def _on_import_radio_clicked(self):
        self.login_stack.slideInWidget(self.import_page)
        self.ui.info_label.setText(self.info_message[self.import_index])
        self.ui.back_button.setEnabled(True)
        self.ui.next_button.setEnabled(self.import_page.is_valid())

    @Slot()
    def _on_back_clicked(self):
        self.ui.back_button.setEnabled(False)
        self.ui.next_button.setEnabled(True)
        self.ui.info_label.setText(self.info_message[self.landing_index])
        self.login_stack.slideInWidget(self.landing_page)

    @Slot()
    def _on_next_clicked(self):
        if self.login_stack.currentWidget() is self.landing_page:
            if self.landing_page.ui.login_browser_radio.isChecked():
                self._on_browser_radio_clicked()
            if self.landing_page.ui.login_import_radio.isChecked():
                self._on_import_radio_clicked()
        elif self.login_stack.currentWidget() is self.browser_page:
            self.browser_page.do_login()
        elif self.login_stack.currentWidget() is self.import_page:
            self.import_page.do_login()

    def login(self):
        if self.args.test_start:
            self.reject()
        self.open()

    @Slot()
    def _on_login_successful(self):
        try:
            if not self.core.login():
                raise ValueError("Login failed.")
            self.logged_in = True
            self.accept()
        except Exception as e:
            self.logger.error(str(e))
            self.core.lgd.invalidate_userdata()
            self.ui.next_button.setEnabled(False)
            self.logged_in = False
            QMessageBox.warning(None, self.tr("Login error"), str(e))

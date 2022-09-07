from dataclasses import dataclass
from logging import getLogger

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLayout, QDialog, QMessageBox, QFrame
from legendary.core import LegendaryCore

from rare.shared import ArgumentsSingleton
from rare.ui.components.dialogs.login.landing_page import Ui_LandingPage
from rare.ui.components.dialogs.login.login_dialog import Ui_LoginDialog
from rare.widgets.sliding_stack import SlidingStackedWidget
from .browser_login import BrowserLogin
from .import_login import ImportLogin

logger = getLogger("LoginDialog")


@dataclass
class LoginPages:
    landing: int
    browser: int
    import_egl: int


class LandingPage(QFrame):
    def __init__(self, parent=None):
        super(LandingPage, self).__init__(parent=parent)
        self.setFrameStyle(self.StyledPanel)
        self.ui = Ui_LandingPage()
        self.ui.setupUi(self)


class LoginDialog(QDialog):
    logged_in: bool = False
    pages = LoginPages(landing=0, browser=1, import_egl=2)

    def __init__(self, core: LegendaryCore, parent=None):
        super(LoginDialog, self).__init__(parent=parent)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(
            Qt.Window
            | Qt.Dialog
            | Qt.CustomizeWindowHint
            | Qt.WindowSystemMenuHint
            | Qt.WindowTitleHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowCloseButtonHint
            | Qt.MSWindowsFixedSizeDialogHint
        )
        self.setWindowModality(Qt.WindowModal)
        self.ui = Ui_LoginDialog()
        self.ui.setupUi(self)

        self.core = core
        self.args = ArgumentsSingleton()

        self.login_stack = SlidingStackedWidget(parent=self)
        self.login_stack.setMinimumSize(480, 180)
        self.ui.login_stack_layout.addWidget(self.login_stack)

        self.landing_page = LandingPage(self.login_stack)
        self.login_stack.insertWidget(self.pages.landing, self.landing_page)

        self.browser_page = BrowserLogin(self.core, self.login_stack)
        self.login_stack.insertWidget(self.pages.browser, self.browser_page)
        self.browser_page.success.connect(self.login_successful)
        self.browser_page.changed.connect(
            lambda: self.ui.next_button.setEnabled(self.browser_page.is_valid())
        )
        self.import_page = ImportLogin(self.core, self.login_stack)
        self.login_stack.insertWidget(self.pages.import_egl, self.import_page)
        self.import_page.success.connect(self.login_successful)
        self.import_page.changed.connect(lambda: self.ui.next_button.setEnabled(self.import_page.is_valid()))

        self.ui.next_button.setEnabled(False)
        self.ui.back_button.setEnabled(False)

        self.landing_page.ui.login_browser_radio.clicked.connect(lambda: self.ui.next_button.setEnabled(True))
        self.landing_page.ui.login_browser_radio.clicked.connect(self.browser_radio_clicked)
        self.landing_page.ui.login_import_radio.clicked.connect(lambda: self.ui.next_button.setEnabled(True))
        self.landing_page.ui.login_import_radio.clicked.connect(self.import_radio_clicked)

        self.ui.exit_button.clicked.connect(self.close)
        self.ui.back_button.clicked.connect(self.back_clicked)
        self.ui.next_button.clicked.connect(self.next_clicked)

        self.login_stack.setCurrentIndex(self.pages.landing)

        self.layout().setSizeConstraint(QLayout.SetFixedSize)

    def back_clicked(self):
        self.ui.back_button.setEnabled(False)
        self.ui.next_button.setEnabled(True)
        self.login_stack.slideInIndex(self.pages.landing)

    def browser_radio_clicked(self):
        self.login_stack.slideInIndex(self.pages.browser)
        self.ui.back_button.setEnabled(True)
        self.ui.next_button.setEnabled(False)

    def import_radio_clicked(self):
        self.login_stack.slideInIndex(self.pages.import_egl)
        self.ui.back_button.setEnabled(True)
        self.ui.next_button.setEnabled(self.import_page.is_valid())

    def next_clicked(self):
        if self.login_stack.currentIndex() == self.pages.landing:
            if self.landing_page.ui.login_browser_radio.isChecked():
                self.browser_radio_clicked()
            if self.landing_page.ui.login_import_radio.isChecked():
                self.import_radio_clicked()
        elif self.login_stack.currentIndex() == self.pages.browser:
            self.browser_page.do_login()
        elif self.login_stack.currentIndex() == self.pages.import_egl:
            self.import_page.do_login()

    def login(self):
        if self.args.test_start:
            return False
        self.exec_()
        return self.logged_in

    def login_successful(self):
        try:
            if self.core.login():
                self.logged_in = True
                self.close()
            else:
                raise ValueError("Login failed.")
        except Exception as e:
            logger.error(str(e))
            self.core.lgd.invalidate_userdata()
            self.ui.next_button.setEnabled(False)
            self.logged_in = False
            QMessageBox.warning(None, self.tr("Login error"), str(e))

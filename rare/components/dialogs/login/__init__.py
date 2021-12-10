from dataclasses import dataclass
from logging import getLogger

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSizePolicy, QLayout, QDialog, QMessageBox

from legendary.core import LegendaryCore
from rare import shared
from rare.components.dialogs.login.browser_login import BrowserLogin
from rare.components.dialogs.login.import_login import ImportLogin
from rare.ui.components.dialogs.login.login_dialog import Ui_LoginDialog

logger = getLogger("Login")


@dataclass
class LoginPages:
    landing: int
    browser: int
    import_egl: int


class LoginDialog(QDialog, Ui_LoginDialog):
    logged_in: bool = False
    pages = LoginPages(landing=0, browser=1, import_egl=2)

    def __init__(self, core: LegendaryCore, parent=None):
        super(LoginDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)

        self.core = core

        self.browser_page = BrowserLogin(self.core, self.login_stack)
        self.login_stack.insertWidget(self.pages.browser, self.browser_page)
        self.browser_page.success.connect(self.login_successful)
        self.browser_page.changed.connect(
            lambda: self.next_button.setEnabled(self.browser_page.is_valid())
        )
        self.import_page = ImportLogin(self.core, self.login_stack)
        self.login_stack.insertWidget(self.pages.import_egl, self.import_page)
        self.import_page.success.connect(self.login_successful)
        self.import_page.changed.connect(
            lambda: self.next_button.setEnabled(self.import_page.is_valid())
        )

        self.next_button.setEnabled(False)
        self.back_button.setEnabled(False)

        self.login_browser_radio.clicked.connect(lambda: self.next_button.setEnabled(True))
        self.login_import_radio.clicked.connect(lambda: self.next_button.setEnabled(True))
        self.exit_button.clicked.connect(self.close)
        self.back_button.clicked.connect(self.back_clicked)
        self.next_button.clicked.connect(self.next_clicked)

        self.login_stack.setCurrentIndex(self.pages.landing)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.dialog_layout.setSizeConstraint(QLayout.SetFixedSize)
        # self.resize(self.minimumSizeHint())

    def back_clicked(self):
        self.back_button.setEnabled(False)
        self.next_button.setEnabled(True)
        self.login_stack.setCurrentIndex(self.pages.landing)

    def next_clicked(self):
        if self.login_stack.currentIndex() == self.pages.landing:
            if self.login_browser_radio.isChecked():
                self.login_stack.setCurrentIndex(self.pages.browser)
                self.next_button.setEnabled(False)
            if self.login_import_radio.isChecked():
                self.login_stack.setCurrentIndex(self.pages.import_egl)
                self.next_button.setEnabled(self.import_page.is_valid())
            self.back_button.setEnabled(True)
        elif self.login_stack.currentIndex() == self.pages.browser:
            self.browser_page.do_login()
        elif self.login_stack.currentIndex() == self.pages.import_egl:
            self.import_page.do_login()

    def login(self):
        if shared.args.test_start:
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
        except ValueError as e:
            logger.error(str(e))
            self.next_button.setEnabled(False)
            self.logged_in = False
            QMessageBox.warning(self, "Error", str(e))


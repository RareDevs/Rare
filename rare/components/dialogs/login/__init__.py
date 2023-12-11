from logging import getLogger

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QLayout, QDialog, QMessageBox, QFrame
from legendary.core import LegendaryCore

from rare.shared import ArgumentsSingleton
from rare.ui.components.dialogs.login.landing_page import Ui_LandingPage
from rare.ui.components.dialogs.login.login_dialog import Ui_LoginDialog
from rare.widgets.sliding_stack import SlidingStackedWidget
from .browser_login import BrowserLogin
from .import_login import ImportLogin

logger = getLogger("LoginDialog")


class LandingPage(QFrame):
    def __init__(self, parent=None):
        super(LandingPage, self).__init__(parent=parent)
        self.setFrameStyle(self.StyledPanel)
        self.ui = Ui_LandingPage()
        self.ui.setupUi(self)


class LoginDialog(QDialog):
    exit_app: pyqtSignal = pyqtSignal(int)

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

        self.logged_in: bool = False

        self.core = core
        self.args = ArgumentsSingleton()

        self.login_stack = SlidingStackedWidget(parent=self)
        self.login_stack.setMinimumWidth(480)
        self.ui.login_stack_layout.addWidget(self.login_stack)

        self.landing_page = LandingPage(self.login_stack)
        self.login_stack.insertWidget(0, self.landing_page)

        self.browser_page = BrowserLogin(self.core, self.login_stack)
        self.login_stack.insertWidget(1, self.browser_page)
        self.browser_page.success.connect(self.login_successful)
        self.browser_page.changed.connect(
            lambda: self.ui.next_button.setEnabled(self.browser_page.is_valid())
        )
        self.import_page = ImportLogin(self.core, self.login_stack)
        self.login_stack.insertWidget(2, self.import_page)
        self.import_page.success.connect(self.login_successful)
        self.import_page.changed.connect(lambda: self.ui.next_button.setEnabled(self.import_page.is_valid()))

        # # NOTE: The real problem is that the BrowserLogin page has a huge QLabel with word-wrapping enabled.
        # # That forces the whole form to vertically expand instead of horizontally. Since the form is not shown
        # # on the first page, the internal Qt calculation for the size of that form calculates it by expanding it
        # # vertically. Once the form becomes visible, the correct calculation takes place and that is why the
        # # dialog reduces in height. To avoid that, calculate the bounding size of all forms and set it as the
        # # minumum size
        # self.login_stack.setMinimumSize(
        #     self.landing_page.sizeHint().expandedTo(
        #         self.browser_page.sizeHint().expandedTo(self.import_page.sizeHint())
        #     )
        # )

        self.login_stack.setFixedHeight(
            max(
                self.landing_page.heightForWidth(self.login_stack.minimumWidth()),
                self.browser_page.heightForWidth(self.login_stack.minimumWidth()),
                self.import_page.heightForWidth(self.login_stack.minimumWidth()),
            )
        )

        self.ui.next_button.setEnabled(False)
        self.ui.back_button.setEnabled(False)

        self.landing_page.ui.login_browser_radio.clicked.connect(lambda: self.ui.next_button.setEnabled(True))
        self.landing_page.ui.login_browser_radio.clicked.connect(self.browser_radio_clicked)
        self.landing_page.ui.login_import_radio.clicked.connect(lambda: self.ui.next_button.setEnabled(True))
        self.landing_page.ui.login_import_radio.clicked.connect(self.import_radio_clicked)

        self.ui.exit_button.clicked.connect(self.close)
        self.ui.back_button.clicked.connect(self.back_clicked)
        self.ui.next_button.clicked.connect(self.next_clicked)

        self.login_stack.setCurrentWidget(self.landing_page)

        self.layout().setSizeConstraint(QLayout.SetFixedSize)

    def back_clicked(self):
        self.ui.back_button.setEnabled(False)
        self.ui.next_button.setEnabled(True)
        self.login_stack.slideInWidget(self.landing_page)

    def browser_radio_clicked(self):
        self.login_stack.slideInWidget(self.browser_page)
        self.ui.back_button.setEnabled(True)
        self.ui.next_button.setEnabled(False)

    def import_radio_clicked(self):
        self.login_stack.slideInWidget(self.import_page)
        self.ui.back_button.setEnabled(True)
        self.ui.next_button.setEnabled(self.import_page.is_valid())

    def next_clicked(self):
        if self.login_stack.currentWidget() is self.landing_page:
            if self.landing_page.ui.login_browser_radio.isChecked():
                self.browser_radio_clicked()
            if self.landing_page.ui.login_import_radio.isChecked():
                self.import_radio_clicked()
        elif self.login_stack.currentWidget() is self.browser_page:
            self.browser_page.do_login()
        elif self.login_stack.currentWidget() is self.import_page:
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

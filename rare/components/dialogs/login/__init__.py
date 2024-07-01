from logging import getLogger

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QLayout, QMessageBox, QFrame
from legendary.core import LegendaryCore

from rare.shared import ArgumentsSingleton
from rare.ui.components.dialogs.login.landing_page import Ui_LandingPage
from rare.ui.components.dialogs.login.login_dialog import Ui_LoginDialog
from rare.utils.misc import qta_icon
from rare.widgets.dialogs import BaseDialog
from rare.widgets.sliding_stack import SlidingStackedWidget
from .browser_login import BrowserLogin
from .import_login import ImportLogin

logger = getLogger("LoginDialog")


class LandingPage(QFrame):
    def __init__(self, parent=None):
        super(LandingPage, self).__init__(parent=parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.ui = Ui_LandingPage()
        self.ui.setupUi(self)


class LoginDialog(BaseDialog):

    def __init__(self, core: LegendaryCore, parent=None):
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
        self.browser_page.isValid.connect(lambda x: self.ui.next_button.setEnabled(x))
        self.import_page = ImportLogin(self.core, self.login_stack)
        self.login_stack.insertWidget(2, self.import_page)
        self.import_page.success.connect(self.login_successful)
        self.import_page.isValid.connect(lambda x: self.ui.next_button.setEnabled(x))

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

        self.ui.exit_button.clicked.connect(self.reject)
        self.ui.back_button.clicked.connect(self.back_clicked)
        self.ui.next_button.clicked.connect(self.next_clicked)

        self.login_stack.setCurrentWidget(self.landing_page)

        self.ui.exit_button.setIcon(qta_icon("fa.remove"))
        self.ui.back_button.setIcon(qta_icon("fa.chevron-left"))
        self.ui.next_button.setIcon(qta_icon("fa.chevron-right"))

        # lk: Set next as the default button only to stop closing the dialog when pressing enter
        self.ui.exit_button.setAutoDefault(False)
        self.ui.back_button.setAutoDefault(False)
        self.ui.next_button.setAutoDefault(True)

        self.ui.main_layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    @Slot()
    def browser_radio_clicked(self):
        self.login_stack.slideInWidget(self.browser_page)
        self.ui.back_button.setEnabled(True)
        self.ui.next_button.setEnabled(False)

    @Slot()
    def import_radio_clicked(self):
        self.login_stack.slideInWidget(self.import_page)
        self.ui.back_button.setEnabled(True)
        self.ui.next_button.setEnabled(self.import_page.is_valid())

    @Slot()
    def back_clicked(self):
        self.ui.back_button.setEnabled(False)
        self.ui.next_button.setEnabled(True)
        self.login_stack.slideInWidget(self.landing_page)

    @Slot()
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
            self.reject()
        self.open()

    @Slot()
    def login_successful(self):
        try:
            if not self.core.login():
                raise ValueError("Login failed.")
            self.logged_in = True
            self.accept()
        except Exception as e:
            logger.error(str(e))
            self.core.lgd.invalidate_userdata()
            self.ui.next_button.setEnabled(False)
            self.logged_in = False
            QMessageBox.warning(None, self.tr("Login error"), str(e))


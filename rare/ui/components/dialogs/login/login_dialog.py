
################################################################################
## Form generated from reading UI file 'login_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)


class Ui_LoginDialog:
    def setupUi(self, LoginDialog):
        if not LoginDialog.objectName():
            LoginDialog.setObjectName("LoginDialog")
        LoginDialog.resize(242, 146)
        self.main_layout = QVBoxLayout(LoginDialog)
        self.main_layout.setObjectName("main_layout")
        self.login_vspacer_top = QSpacerItem(17, 17, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.main_layout.addItem(self.login_vspacer_top)

        self.welcome_label = QLabel(LoginDialog)
        self.welcome_label.setObjectName("welcome_label")

        self.main_layout.addWidget(self.welcome_label)

        self.login_vspacer_bottom = QSpacerItem(17, 17, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.main_layout.addItem(self.login_vspacer_bottom)

        self.info_label = QLabel(LoginDialog)
        self.info_label.setObjectName("info_label")
        self.info_label.setFrameShape(QFrame.Shape.StyledPanel)
        self.info_label.setFrameShadow(QFrame.Shadow.Sunken)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.info_label.setWordWrap(True)

        self.main_layout.addWidget(self.info_label)

        self.button_layout = QHBoxLayout()
        self.button_layout.setObjectName("button_layout")
        self.exit_button = QPushButton(LoginDialog)
        self.exit_button.setObjectName("exit_button")

        self.button_layout.addWidget(self.exit_button)

        self.button_hspacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.button_layout.addItem(self.button_hspacer)

        self.back_button = QPushButton(LoginDialog)
        self.back_button.setObjectName("back_button")

        self.button_layout.addWidget(self.back_button)

        self.next_button = QPushButton(LoginDialog)
        self.next_button.setObjectName("next_button")

        self.button_layout.addWidget(self.next_button)


        self.main_layout.addLayout(self.button_layout)


        self.retranslateUi(LoginDialog)
    # setupUi

    def retranslateUi(self, LoginDialog):
        LoginDialog.setWindowTitle(QCoreApplication.translate("LoginDialog", "Login", None))
        self.welcome_label.setText(QCoreApplication.translate("LoginDialog", "<h1>Welcome to Rare</h1>", None))
        self.info_label.setText("")
        self.exit_button.setText(QCoreApplication.translate("LoginDialog", "Exit", None))
        self.back_button.setText(QCoreApplication.translate("LoginDialog", "Back", None))
        self.next_button.setText(QCoreApplication.translate("LoginDialog", "Next", None))
    # retranslateUi


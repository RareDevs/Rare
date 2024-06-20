# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'login_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_LoginDialog(object):
    def setupUi(self, LoginDialog):
        if not LoginDialog.objectName():
            LoginDialog.setObjectName(u"LoginDialog")
        LoginDialog.resize(241, 128)
        self.main_layout = QVBoxLayout(LoginDialog)
        self.main_layout.setObjectName(u"main_layout")
        self.login_vspacer_top = QSpacerItem(0, 17, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.main_layout.addItem(self.login_vspacer_top)

        self.welcome_label = QLabel(LoginDialog)
        self.welcome_label.setObjectName(u"welcome_label")

        self.main_layout.addWidget(self.welcome_label)

        self.login_vspacer_bottom = QSpacerItem(0, 17, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.main_layout.addItem(self.login_vspacer_bottom)

        self.login_stack_layout = QVBoxLayout()
        self.login_stack_layout.setObjectName(u"login_stack_layout")

        self.main_layout.addLayout(self.login_stack_layout)

        self.button_layout = QHBoxLayout()
        self.button_layout.setObjectName(u"button_layout")
        self.exit_button = QPushButton(LoginDialog)
        self.exit_button.setObjectName(u"exit_button")

        self.button_layout.addWidget(self.exit_button)

        self.button_hspacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.button_layout.addItem(self.button_hspacer)

        self.back_button = QPushButton(LoginDialog)
        self.back_button.setObjectName(u"back_button")

        self.button_layout.addWidget(self.back_button)

        self.next_button = QPushButton(LoginDialog)
        self.next_button.setObjectName(u"next_button")

        self.button_layout.addWidget(self.next_button)


        self.main_layout.addLayout(self.button_layout)


        self.retranslateUi(LoginDialog)
    # setupUi

    def retranslateUi(self, LoginDialog):
        LoginDialog.setWindowTitle(QCoreApplication.translate("LoginDialog", u"Login", None))
        self.welcome_label.setText(QCoreApplication.translate("LoginDialog", u"<h1>Welcome to Rare</h1>", None))
        self.exit_button.setText(QCoreApplication.translate("LoginDialog", u"Exit", None))
        self.back_button.setText(QCoreApplication.translate("LoginDialog", u"Back", None))
        self.next_button.setText(QCoreApplication.translate("LoginDialog", u"Next", None))
    # retranslateUi


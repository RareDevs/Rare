# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'browser_login.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class Ui_BrowserLogin(object):
    def setupUi(self, BrowserLogin):
        if not BrowserLogin.objectName():
            BrowserLogin.setObjectName(u"BrowserLogin")
        BrowserLogin.resize(310, 237)
        BrowserLogin.setWindowTitle(u"BrowserLogin")
        self.main_layout = QVBoxLayout(BrowserLogin)
        self.main_layout.setObjectName(u"main_layout")
        self.title_label = QLabel(BrowserLogin)
        self.title_label.setObjectName(u"title_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.title_label.sizePolicy().hasHeightForWidth())
        self.title_label.setSizePolicy(sizePolicy)
        font = QFont()
        font.setBold(True)
        self.title_label.setFont(font)

        self.main_layout.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignTop)

        self.form_widget = QWidget(BrowserLogin)
        self.form_widget.setObjectName(u"form_widget")
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setObjectName(u"form_layout")
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.open_button = QPushButton(self.form_widget)
        self.open_button.setObjectName(u"open_button")

        self.form_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.open_button)

        self.link_layout = QHBoxLayout()
        self.link_layout.setObjectName(u"link_layout")
        self.link_layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.link_text = QLineEdit(self.form_widget)
        self.link_text.setObjectName(u"link_text")
        self.link_text.setText(u"")
        self.link_text.setReadOnly(True)
        self.link_text.setPlaceholderText(u"")

        self.link_layout.addWidget(self.link_text)

        self.copy_button = QPushButton(self.form_widget)
        self.copy_button.setObjectName(u"copy_button")
        self.copy_button.setText(u"")

        self.link_layout.addWidget(self.copy_button)

        self.link_layout.setStretch(0, 1)

        self.form_layout.setLayout(0, QFormLayout.ItemRole.FieldRole, self.link_layout)

        self.sid_label = QLabel(self.form_widget)
        self.sid_label.setObjectName(u"sid_label")
        self.sid_label.setText(u"authorizationCode")
        self.sid_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.form_layout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.sid_label)

        self.status_field = QLabel(self.form_widget)
        self.status_field.setObjectName(u"status_field")
        self.status_field.setFrameShape(QFrame.Shape.StyledPanel)
        self.status_field.setFrameShadow(QFrame.Shadow.Sunken)
        self.status_field.setText(u"")
        self.status_field.setWordWrap(True)

        self.form_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.status_field)

        self.status_label = QLabel(self.form_widget)
        self.status_label.setObjectName(u"status_label")

        self.form_layout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.status_label)


        self.main_layout.addWidget(self.form_widget, 0, Qt.AlignmentFlag.AlignTop)

        self.main_layout.setStretch(1, 1)

        self.retranslateUi(BrowserLogin)
    # setupUi

    def retranslateUi(self, BrowserLogin):
        self.title_label.setText(QCoreApplication.translate("BrowserLogin", u"Login through browser", None))
        self.open_button.setText(QCoreApplication.translate("BrowserLogin", u"Open Browser", None))
        self.status_label.setText(QCoreApplication.translate("BrowserLogin", u"Status", None))
        pass
    # retranslateUi


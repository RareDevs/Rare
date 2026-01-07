# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'landing_page.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFormLayout, QLabel, QRadioButton, QSizePolicy, QVBoxLayout, QWidget


class Ui_LandingPage(object):
    def setupUi(self, LandingPage):
        if not LandingPage.objectName():
            LandingPage.setObjectName(u"LandingPage")
        LandingPage.resize(300, 95)
        LandingPage.setWindowTitle(u"LandingPage")
        self.main_layout = QVBoxLayout(LandingPage)
        self.main_layout.setObjectName(u"main_layout")
        self.login_label = QLabel(LandingPage)
        self.login_label.setObjectName(u"login_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.login_label.sizePolicy().hasHeightForWidth())
        self.login_label.setSizePolicy(sizePolicy)
        font = QFont()
        font.setBold(True)
        self.login_label.setFont(font)

        self.main_layout.addWidget(self.login_label)

        self.form_widget = QWidget(LandingPage)
        self.form_widget.setObjectName(u"form_widget")
        self.form_widget.setMinimumSize(QSize(0, 20))
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setObjectName(u"form_layout")
        self.form_layout.setHorizontalSpacing(15)
        self.form_layout.setVerticalSpacing(5)
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.login_browser_radio = QRadioButton(self.form_widget)
        self.login_browser_radio.setObjectName(u"login_browser_radio")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.login_browser_radio.sizePolicy().hasHeightForWidth())
        self.login_browser_radio.setSizePolicy(sizePolicy1)

        self.form_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.login_browser_radio)

        self.login_browser_label = QLabel(self.form_widget)
        self.login_browser_label.setObjectName(u"login_browser_label")
        font1 = QFont()
        font1.setItalic(True)
        self.login_browser_label.setFont(font1)

        self.form_layout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.login_browser_label)

        self.login_import_radio = QRadioButton(self.form_widget)
        self.login_import_radio.setObjectName(u"login_import_radio")
        sizePolicy1.setHeightForWidth(self.login_import_radio.sizePolicy().hasHeightForWidth())
        self.login_import_radio.setSizePolicy(sizePolicy1)

        self.form_layout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.login_import_radio)

        self.login_import_label = QLabel(self.form_widget)
        self.login_import_label.setObjectName(u"login_import_label")
        self.login_import_label.setFont(font1)

        self.form_layout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.login_import_label)


        self.main_layout.addWidget(self.form_widget)


        self.retranslateUi(LandingPage)
    # setupUi

    def retranslateUi(self, LandingPage):
        self.login_label.setText(QCoreApplication.translate("LandingPage", u"Select login method", None))
        self.login_browser_radio.setText(QCoreApplication.translate("LandingPage", u"Browser", None))
        self.login_browser_label.setText(QCoreApplication.translate("LandingPage", u"Login using a browser.", None))
        self.login_import_radio.setText(QCoreApplication.translate("LandingPage", u"Import", None))
        self.login_import_label.setText(QCoreApplication.translate("LandingPage", u"Import from Epic Games Launcher", None))
        pass
    # retranslateUi


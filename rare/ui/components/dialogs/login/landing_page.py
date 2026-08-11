
################################################################################
## Form generated from reading UI file 'landing_page.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFormLayout, QLabel, QRadioButton, QSizePolicy, QVBoxLayout, QWidget


class Ui_LandingPage:
    def setupUi(self, LandingPage):
        if not LandingPage.objectName():
            LandingPage.setObjectName("LandingPage")
        LandingPage.resize(300, 95)
        LandingPage.setWindowTitle("LandingPage")
        self.main_layout = QVBoxLayout(LandingPage)
        self.main_layout.setObjectName("main_layout")
        self.login_label = QLabel(LandingPage)
        self.login_label.setObjectName("login_label")
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
        self.form_widget.setObjectName("form_widget")
        self.form_widget.setMinimumSize(QSize(0, 20))
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setObjectName("form_layout")
        self.form_layout.setHorizontalSpacing(15)
        self.form_layout.setVerticalSpacing(5)
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.login_browser_radio = QRadioButton(self.form_widget)
        self.login_browser_radio.setObjectName("login_browser_radio")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.login_browser_radio.sizePolicy().hasHeightForWidth())
        self.login_browser_radio.setSizePolicy(sizePolicy1)

        self.form_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.login_browser_radio)

        self.login_browser_label = QLabel(self.form_widget)
        self.login_browser_label.setObjectName("login_browser_label")
        font1 = QFont()
        font1.setItalic(True)
        self.login_browser_label.setFont(font1)

        self.form_layout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.login_browser_label)

        self.login_import_radio = QRadioButton(self.form_widget)
        self.login_import_radio.setObjectName("login_import_radio")
        sizePolicy1.setHeightForWidth(self.login_import_radio.sizePolicy().hasHeightForWidth())
        self.login_import_radio.setSizePolicy(sizePolicy1)

        self.form_layout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.login_import_radio)

        self.login_import_label = QLabel(self.form_widget)
        self.login_import_label.setObjectName("login_import_label")
        self.login_import_label.setFont(font1)

        self.form_layout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.login_import_label)


        self.main_layout.addWidget(self.form_widget)


        self.retranslateUi(LandingPage)
    # setupUi

    def retranslateUi(self, LandingPage):
        self.login_label.setText(QCoreApplication.translate("LandingPage", "Select login method", None))
        self.login_browser_radio.setText(QCoreApplication.translate("LandingPage", "Browser", None))
        self.login_browser_label.setText(QCoreApplication.translate("LandingPage", "Login using a browser.", None))
        self.login_import_radio.setText(QCoreApplication.translate("LandingPage", "Import", None))
        self.login_import_label.setText(QCoreApplication.translate("LandingPage", "Import from Epic Games Launcher", None))
    # retranslateUi


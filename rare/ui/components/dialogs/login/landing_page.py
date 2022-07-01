# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'rare/ui/components/dialogs/login/landing_page.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_LandingPage(object):
    def setupUi(self, LandingPage):
        LandingPage.setObjectName("LandingPage")
        LandingPage.resize(400, 200)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(LandingPage.sizePolicy().hasHeightForWidth())
        LandingPage.setSizePolicy(sizePolicy)
        self.landing_layout = QtWidgets.QGridLayout(LandingPage)
        self.landing_layout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.landing_layout.setObjectName("landing_layout")
        self.login_label = QtWidgets.QLabel(LandingPage)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.login_label.setFont(font)
        self.login_label.setObjectName("login_label")
        self.landing_layout.addWidget(self.login_label, 0, 0, 1, 3)
        self.login_browser_radio = QtWidgets.QRadioButton(LandingPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.login_browser_radio.sizePolicy().hasHeightForWidth())
        self.login_browser_radio.setSizePolicy(sizePolicy)
        self.login_browser_radio.setObjectName("login_browser_radio")
        self.landing_layout.addWidget(self.login_browser_radio, 1, 0, 1, 1)
        self.login_browser_label = QtWidgets.QLabel(LandingPage)
        font = QtGui.QFont()
        font.setItalic(True)
        self.login_browser_label.setFont(font)
        self.login_browser_label.setObjectName("login_browser_label")
        self.landing_layout.addWidget(self.login_browser_label, 1, 1, 1, 1)
        self.login_import_radio = QtWidgets.QRadioButton(LandingPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.login_import_radio.sizePolicy().hasHeightForWidth())
        self.login_import_radio.setSizePolicy(sizePolicy)
        self.login_import_radio.setObjectName("login_import_radio")
        self.landing_layout.addWidget(self.login_import_radio, 2, 0, 1, 1)
        self.login_import_label = QtWidgets.QLabel(LandingPage)
        font = QtGui.QFont()
        font.setItalic(True)
        self.login_import_label.setFont(font)
        self.login_import_label.setObjectName("login_import_label")
        self.landing_layout.addWidget(self.login_import_label, 2, 1, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.landing_layout.addItem(spacerItem, 1, 2, 2, 1)
        self.landing_layout.setRowStretch(1, 1)
        self.landing_layout.setRowStretch(2, 1)

        self.retranslateUi(LandingPage)
        QtCore.QMetaObject.connectSlotsByName(LandingPage)

    def retranslateUi(self, LandingPage):
        _translate = QtCore.QCoreApplication.translate
        LandingPage.setWindowTitle(_translate("LandingPage", "LandingPage"))
        self.login_label.setText(_translate("LandingPage", "Select login method"))
        self.login_browser_radio.setText(_translate("LandingPage", "Browser"))
        self.login_browser_label.setText(_translate("LandingPage", "Login using a browser."))
        self.login_import_radio.setText(_translate("LandingPage", "Import"))
        self.login_import_label.setText(_translate("LandingPage", "Import from Epic Games Launcher"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    LandingPage = QtWidgets.QWidget()
    ui = Ui_LandingPage()
    ui.setupUi(LandingPage)
    LandingPage.show()
    sys.exit(app.exec_())
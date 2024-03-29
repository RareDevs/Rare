# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'rare/ui/components/tabs/settings/about.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_About(object):
    def setupUi(self, About):
        About.setObjectName("About")
        About.resize(507, 210)
        self.about_layout = QtWidgets.QFormLayout(About)
        self.about_layout.setLabelAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.about_layout.setObjectName("about_layout")
        self.version_label = QtWidgets.QLabel(About)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.version_label.setFont(font)
        self.version_label.setObjectName("version_label")
        self.about_layout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.version_label)
        self.version = QtWidgets.QLabel(About)
        self.version.setText("error")
        self.version.setObjectName("version")
        self.about_layout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.version)
        self.update_label = QtWidgets.QLabel(About)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.update_label.setFont(font)
        self.update_label.setObjectName("update_label")
        self.about_layout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.update_label)
        self.update_lbl = QtWidgets.QLabel(About)
        self.update_lbl.setText("error")
        self.update_lbl.setObjectName("update_lbl")
        self.about_layout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.update_lbl)
        self.open_browser = QtWidgets.QPushButton(About)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.open_browser.sizePolicy().hasHeightForWidth())
        self.open_browser.setSizePolicy(sizePolicy)
        self.open_browser.setObjectName("open_browser")
        self.about_layout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.open_browser)
        self.dev_label = QtWidgets.QLabel(About)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.dev_label.setFont(font)
        self.dev_label.setObjectName("dev_label")
        self.about_layout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.dev_label)
        self.dev = QtWidgets.QLabel(About)
        self.dev.setText("<a href=\'https://github.com/Dummerle\' style=\'color: #2980b9; text-decoration:none\'>Dummerle</a>\n"
"<br>\n"
"<a href=\'https://github.com/loathingkernel\' style=\'color: #2980b9; text-decoration:none\'>loathingkernel</a>")
        self.dev.setOpenExternalLinks(True)
        self.dev.setObjectName("dev")
        self.about_layout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.dev)
        self.lgd_dev_label = QtWidgets.QLabel(About)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.lgd_dev_label.setFont(font)
        self.lgd_dev_label.setObjectName("lgd_dev_label")
        self.about_layout.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.lgd_dev_label)
        self.lgd_dev = QtWidgets.QLabel(About)
        self.lgd_dev.setText("<a href=\'https://github.com/derrod/\' style=\'color: #2980b9; text-decoration:none\'>derrod</a>")
        self.lgd_dev.setOpenExternalLinks(True)
        self.lgd_dev.setObjectName("lgd_dev")
        self.about_layout.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.lgd_dev)
        self.license_label = QtWidgets.QLabel(About)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.license_label.setFont(font)
        self.license_label.setObjectName("license_label")
        self.about_layout.setWidget(6, QtWidgets.QFormLayout.LabelRole, self.license_label)
        self.license = QtWidgets.QLabel(About)
        self.license.setObjectName("license")
        self.about_layout.setWidget(6, QtWidgets.QFormLayout.FieldRole, self.license)
        self.contrib_label = QtWidgets.QLabel(About)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.contrib_label.setFont(font)
        self.contrib_label.setObjectName("contrib_label")
        self.about_layout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.contrib_label)
        self.label = QtWidgets.QLabel(About)
        self.label.setText("<a href=\'https://github.com/MultisampledNight\' style=\'color: #2980b9; text-decoration:none\'>MultisampledNight</a> <i>artwork, bug hunting, testing</i>\n"
"<br>\n"
"<a href=\'https://github.com/invertedEcho\' style=\'color: #2980b9; text-decoration:none\'>invertedEcho</a> <i>moving games, environment variables</i>\n"
"<br>\n"
"<a href=\'https://github.com/ChemicalXandco\' style=\'color: #2980b9; text-decoration:none\'>ChemicalXandco</a> <i>downloads improvements, windows integration</i>\n"
"<br>\n"
"<a href=\'https://github.com/gnanini\' style=\'color: #2980b9; text-decoration:none\'>gnanini</a> <i>steam grades</i>")
        self.label.setObjectName("label")
        self.about_layout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.label)

        self.retranslateUi(About)

    def retranslateUi(self, About):
        _translate = QtCore.QCoreApplication.translate
        About.setWindowTitle(_translate("About", "About"))
        self.version_label.setText(_translate("About", "Version"))
        self.update_label.setText(_translate("About", "Update"))
        self.open_browser.setText(_translate("About", "Download latest release"))
        self.dev_label.setText(_translate("About", "Rare Developers"))
        self.dev.setToolTip(_translate("About", "Github"))
        self.lgd_dev_label.setText(_translate("About", "Legendary Developer"))
        self.lgd_dev.setToolTip(_translate("About", "Github"))
        self.license_label.setText(_translate("About", "License"))
        self.license.setText(_translate("About", "GNU General Public License v3.0"))
        self.contrib_label.setText(_translate("About", "Rare Contributors"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    About = QtWidgets.QWidget()
    ui = Ui_About()
    ui.setupUi(About)
    About.show()
    sys.exit(app.exec_())

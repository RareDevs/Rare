
################################################################################
## Form generated from reading UI file 'about.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFormLayout, QLabel, QPushButton, QSizePolicy


class Ui_About:
    def setupUi(self, About):
        if not About.objectName():
            About.setObjectName("About")
        About.resize(542, 215)
        self.about_layout = QFormLayout(About)
        self.about_layout.setObjectName("about_layout")
        self.about_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.version_label = QLabel(About)
        self.version_label.setObjectName("version_label")
        font = QFont()
        font.setBold(True)
        self.version_label.setFont(font)

        self.about_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.version_label)

        self.version = QLabel(About)
        self.version.setObjectName("version")
        self.version.setText("error")

        self.about_layout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.version)

        self.update_label = QLabel(About)
        self.update_label.setObjectName("update_label")
        self.update_label.setFont(font)

        self.about_layout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.update_label)

        self.update_field = QLabel(About)
        self.update_field.setObjectName("update_field")
        self.update_field.setText("error")

        self.about_layout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.update_field)

        self.open_browser = QPushButton(About)
        self.open_browser.setObjectName("open_browser")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.open_browser.sizePolicy().hasHeightForWidth())
        self.open_browser.setSizePolicy(sizePolicy)

        self.about_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.open_browser)

        self.dev_label = QLabel(About)
        self.dev_label.setObjectName("dev_label")
        self.dev_label.setFont(font)

        self.about_layout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.dev_label)

        self.dev = QLabel(About)
        self.dev.setObjectName("dev")
        self.dev.setText("<a href='https://github.com/Dummerle' style='color: #2980b9; text-decoration:none'>Dummerle</a>\n"
"<br>\n"
"<a href='https://github.com/loathingkernel' style='color: #2980b9; text-decoration:none'>loathingkernel</a>")
        self.dev.setOpenExternalLinks(True)

        self.about_layout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.dev)

        self.lgd_dev_label = QLabel(About)
        self.lgd_dev_label.setObjectName("lgd_dev_label")
        self.lgd_dev_label.setFont(font)

        self.about_layout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.lgd_dev_label)

        self.lgd_dev = QLabel(About)
        self.lgd_dev.setObjectName("lgd_dev")
        self.lgd_dev.setText("<a href='https://github.com/derrod/' style='color: #2980b9; text-decoration:none'>derrod</a>")
        self.lgd_dev.setOpenExternalLinks(True)

        self.about_layout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.lgd_dev)

        self.license_label = QLabel(About)
        self.license_label.setObjectName("license_label")
        self.license_label.setFont(font)

        self.about_layout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.license_label)

        self.license = QLabel(About)
        self.license.setObjectName("license")

        self.about_layout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.license)

        self.contrib_label = QLabel(About)
        self.contrib_label.setObjectName("contrib_label")
        self.contrib_label.setFont(font)

        self.about_layout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.contrib_label)

        self.label = QLabel(About)
        self.label.setObjectName("label")
        self.label.setText("<a href='https://github.com/CommandMC' style='color: #2980b9; text-decoration:none'>CommandMC</a> <i>author of <a href='https://github.com/CommandMC/Rare' style='color: #2980b9; text-decoration:none'>original Rare</a>, the very early base of this project</i>\n"
"<br>\n"
"<a href='https://github.com/MultisampledNight' style='color: #2980b9; text-decoration:none'>MultisampledNight</a> <i>artwork, bug hunting, testing</i>\n"
"<br>\n"
"<a href='https://github.com/invertedEcho' style='color: #2980b9; text-decoration:none'>invertedEcho</a> <i>moving games, environment variables</i>\n"
"<br>\n"
"<a href='https://github.com/ChemicalXandco' style='color: #2980b9; text-decoration:none'>ChemicalXandco</a> <i>downloads improvements, windows integration</i>\n"
"<br>\n"
"<a href='https://github.com/gnanini' style='color: #2980b9; text-decoration:none'>gnanini</a> <i>steam grades</i>")

        self.about_layout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.label)


        self.retranslateUi(About)
    # setupUi

    def retranslateUi(self, About):
        About.setWindowTitle(QCoreApplication.translate("About", "About", None))
        self.version_label.setText(QCoreApplication.translate("About", "Version", None))
        self.update_label.setText(QCoreApplication.translate("About", "Update", None))
        self.open_browser.setText(QCoreApplication.translate("About", "Download latest release", None))
        self.dev_label.setText(QCoreApplication.translate("About", "Rare Developers", None))
#if QT_CONFIG(tooltip)
        self.dev.setToolTip(QCoreApplication.translate("About", "Github", None))
#endif // QT_CONFIG(tooltip)
        self.lgd_dev_label.setText(QCoreApplication.translate("About", "Legendary Developer", None))
#if QT_CONFIG(tooltip)
        self.lgd_dev.setToolTip(QCoreApplication.translate("About", "Github", None))
#endif // QT_CONFIG(tooltip)
        self.license_label.setText(QCoreApplication.translate("About", "License", None))
        self.license.setText(QCoreApplication.translate("About", "GNU General Public License v3.0", None))
        self.contrib_label.setText(QCoreApplication.translate("About", "Rare Contributors", None))
    # retranslateUi


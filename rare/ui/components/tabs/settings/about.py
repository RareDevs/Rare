# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'about.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QLabel, QPushButton,
    QSizePolicy, QWidget)

class Ui_About(object):
    def setupUi(self, About):
        if not About.objectName():
            About.setObjectName(u"About")
        About.resize(507, 210)
        self.about_layout = QFormLayout(About)
        self.about_layout.setObjectName(u"about_layout")
        self.about_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.version_label = QLabel(About)
        self.version_label.setObjectName(u"version_label")
        font = QFont()
        font.setBold(True)
        self.version_label.setFont(font)

        self.about_layout.setWidget(0, QFormLayout.LabelRole, self.version_label)

        self.version = QLabel(About)
        self.version.setObjectName(u"version")
        self.version.setText(u"error")

        self.about_layout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.version)

        self.update_label = QLabel(About)
        self.update_label.setObjectName(u"update_label")
        self.update_label.setFont(font)

        self.about_layout.setWidget(1, QFormLayout.LabelRole, self.update_label)

        self.update_lbl = QLabel(About)
        self.update_lbl.setObjectName(u"update_lbl")
        self.update_lbl.setText(u"error")

        self.about_layout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.update_lbl)

        self.open_browser = QPushButton(About)
        self.open_browser.setObjectName(u"open_browser")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.open_browser.sizePolicy().hasHeightForWidth())
        self.open_browser.setSizePolicy(sizePolicy)

        self.about_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.open_browser)

        self.dev_label = QLabel(About)
        self.dev_label.setObjectName(u"dev_label")
        self.dev_label.setFont(font)

        self.about_layout.setWidget(3, QFormLayout.LabelRole, self.dev_label)

        self.dev = QLabel(About)
        self.dev.setObjectName(u"dev")
        self.dev.setText(u"<a href='https://github.com/Dummerle' style='color: #2980b9; text-decoration:none'>Dummerle</a>\n"
"<br>\n"
"<a href='https://github.com/loathingkernel' style='color: #2980b9; text-decoration:none'>loathingkernel</a>")
        self.dev.setOpenExternalLinks(True)

        self.about_layout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.dev)

        self.lgd_dev_label = QLabel(About)
        self.lgd_dev_label.setObjectName(u"lgd_dev_label")
        self.lgd_dev_label.setFont(font)

        self.about_layout.setWidget(5, QFormLayout.LabelRole, self.lgd_dev_label)

        self.lgd_dev = QLabel(About)
        self.lgd_dev.setObjectName(u"lgd_dev")
        self.lgd_dev.setText(u"<a href='https://github.com/derrod/' style='color: #2980b9; text-decoration:none'>derrod</a>")
        self.lgd_dev.setOpenExternalLinks(True)

        self.about_layout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.lgd_dev)

        self.license_label = QLabel(About)
        self.license_label.setObjectName(u"license_label")
        self.license_label.setFont(font)

        self.about_layout.setWidget(6, QFormLayout.LabelRole, self.license_label)

        self.license = QLabel(About)
        self.license.setObjectName(u"license")

        self.about_layout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.license)

        self.contrib_label = QLabel(About)
        self.contrib_label.setObjectName(u"contrib_label")
        self.contrib_label.setFont(font)

        self.about_layout.setWidget(4, QFormLayout.LabelRole, self.contrib_label)

        self.label = QLabel(About)
        self.label.setObjectName(u"label")
        self.label.setText(u"<a href='https://github.com/MultisampledNight' style='color: #2980b9; text-decoration:none'>MultisampledNight</a> <i>artwork, bug hunting, testing</i>\n"
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
        About.setWindowTitle(QCoreApplication.translate("About", u"About", None))
        self.version_label.setText(QCoreApplication.translate("About", u"Version", None))
        self.update_label.setText(QCoreApplication.translate("About", u"Update", None))
        self.open_browser.setText(QCoreApplication.translate("About", u"Download latest release", None))
        self.dev_label.setText(QCoreApplication.translate("About", u"Rare Developers", None))
#if QT_CONFIG(tooltip)
        self.dev.setToolTip(QCoreApplication.translate("About", u"Github", None))
#endif // QT_CONFIG(tooltip)
        self.lgd_dev_label.setText(QCoreApplication.translate("About", u"Legendary Developer", None))
#if QT_CONFIG(tooltip)
        self.lgd_dev.setToolTip(QCoreApplication.translate("About", u"Github", None))
#endif // QT_CONFIG(tooltip)
        self.license_label.setText(QCoreApplication.translate("About", u"License", None))
        self.license.setText(QCoreApplication.translate("About", u"GNU General Public License v3.0", None))
        self.contrib_label.setText(QCoreApplication.translate("About", u"Rare Contributors", None))
    # retranslateUi


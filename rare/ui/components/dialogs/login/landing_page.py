# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'landing_page.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QLabel, QRadioButton,
    QSizePolicy, QWidget)

class Ui_LandingPage(object):
    def setupUi(self, LandingPage):
        if not LandingPage.objectName():
            LandingPage.setObjectName(u"LandingPage")
        LandingPage.resize(293, 78)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(LandingPage.sizePolicy().hasHeightForWidth())
        LandingPage.setSizePolicy(sizePolicy)
        LandingPage.setWindowTitle(u"LandingPage")
        self.main_layout = QFormLayout(LandingPage)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.main_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.main_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.login_label = QLabel(LandingPage)
        self.login_label.setObjectName(u"login_label")
        sizePolicy.setHeightForWidth(self.login_label.sizePolicy().hasHeightForWidth())
        self.login_label.setSizePolicy(sizePolicy)
        font = QFont()
        font.setBold(True)
        self.login_label.setFont(font)

        self.main_layout.setWidget(0, QFormLayout.SpanningRole, self.login_label)

        self.login_browser_radio = QRadioButton(LandingPage)
        self.login_browser_radio.setObjectName(u"login_browser_radio")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.login_browser_radio.sizePolicy().hasHeightForWidth())
        self.login_browser_radio.setSizePolicy(sizePolicy1)

        self.main_layout.setWidget(1, QFormLayout.LabelRole, self.login_browser_radio)

        self.login_browser_label = QLabel(LandingPage)
        self.login_browser_label.setObjectName(u"login_browser_label")
        font1 = QFont()
        font1.setItalic(True)
        self.login_browser_label.setFont(font1)

        self.main_layout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.login_browser_label)

        self.login_import_radio = QRadioButton(LandingPage)
        self.login_import_radio.setObjectName(u"login_import_radio")
        sizePolicy1.setHeightForWidth(self.login_import_radio.sizePolicy().hasHeightForWidth())
        self.login_import_radio.setSizePolicy(sizePolicy1)

        self.main_layout.setWidget(2, QFormLayout.LabelRole, self.login_import_radio)

        self.login_import_label = QLabel(LandingPage)
        self.login_import_label.setObjectName(u"login_import_label")
        self.login_import_label.setFont(font1)

        self.main_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.login_import_label)


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


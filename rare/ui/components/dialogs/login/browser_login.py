# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'browser_login.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QHBoxLayout, QLabel,
    QLayout, QLineEdit, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_BrowserLogin(object):
    def setupUi(self, BrowserLogin):
        if not BrowserLogin.objectName():
            BrowserLogin.setObjectName(u"BrowserLogin")
        BrowserLogin.resize(320, 243)
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

        self.main_layout.addWidget(self.title_label)

        self.form_layout = QFormLayout()
        self.form_layout.setObjectName(u"form_layout")
        self.form_layout.setSizeConstraint(QLayout.SetFixedSize)
        self.form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.open_button = QPushButton(BrowserLogin)
        self.open_button.setObjectName(u"open_button")

        self.form_layout.setWidget(0, QFormLayout.LabelRole, self.open_button)

        self.link_layout = QHBoxLayout()
        self.link_layout.setObjectName(u"link_layout")
        self.link_text = QLineEdit(BrowserLogin)
        self.link_text.setObjectName(u"link_text")
        self.link_text.setText(u"")
        self.link_text.setReadOnly(True)
        self.link_text.setPlaceholderText(u"")

        self.link_layout.addWidget(self.link_text)

        self.copy_button = QPushButton(BrowserLogin)
        self.copy_button.setObjectName(u"copy_button")
        self.copy_button.setText(u"")

        self.link_layout.addWidget(self.copy_button)

        self.link_layout.setStretch(0, 1)

        self.form_layout.setLayout(0, QFormLayout.ItemRole.FieldRole, self.link_layout)

        self.sid_label = QLabel(BrowserLogin)
        self.sid_label.setObjectName(u"sid_label")
        self.sid_label.setText(u"authorizationCode")
        self.sid_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.form_layout.setWidget(1, QFormLayout.LabelRole, self.sid_label)

        self.status_label = QLabel(BrowserLogin)
        self.status_label.setObjectName(u"status_label")
        font1 = QFont()
        font1.setItalic(True)
        self.status_label.setFont(font1)
        self.status_label.setText(u"")

        self.form_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.status_label)


        self.main_layout.addLayout(self.form_layout)

        self.vscaper = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.main_layout.addItem(self.vscaper)

        self.info_label = QLabel(BrowserLogin)
        self.info_label.setObjectName(u"info_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.info_label.sizePolicy().hasHeightForWidth())
        self.info_label.setSizePolicy(sizePolicy1)
        self.info_label.setWordWrap(True)

        self.main_layout.addWidget(self.info_label)


        self.retranslateUi(BrowserLogin)
    # setupUi

    def retranslateUi(self, BrowserLogin):
        self.title_label.setText(QCoreApplication.translate("BrowserLogin", u"Login through browser", None))
        self.open_button.setText(QCoreApplication.translate("BrowserLogin", u"Open Browser", None))
        self.info_label.setText(QCoreApplication.translate("BrowserLogin", u"<i>Click the <strong>Open Browser</strong> button to open the login page in your web browser or copy the link and paste it in any web browser. After logging in using the browser, copy the text in the quotes after </i><code><b>authorizationCode</b></code><i> in the same line into the empty input above.<br><br><strong>DO NOT SHARE THE INFORMATION IN THE BROWSER PAGE WITH ANYONE IN ANY FORM (TEXT OR SCREENSHOT)!</strong></i>", None))
        pass
    # retranslateUi


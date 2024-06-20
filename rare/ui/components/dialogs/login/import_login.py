# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'import_login.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QHBoxLayout,
    QLabel, QLayout, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_ImportLogin(object):
    def setupUi(self, ImportLogin):
        if not ImportLogin.objectName():
            ImportLogin.setObjectName(u"ImportLogin")
        ImportLogin.resize(256, 143)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ImportLogin.sizePolicy().hasHeightForWidth())
        ImportLogin.setSizePolicy(sizePolicy)
        ImportLogin.setWindowTitle(u"ImportLogin")
        self.main_layout = QVBoxLayout(ImportLogin)
        self.main_layout.setObjectName(u"main_layout")
        self.title_label = QLabel(ImportLogin)
        self.title_label.setObjectName(u"title_label")
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
        self.prefix_layout = QHBoxLayout()
        self.prefix_layout.setObjectName(u"prefix_layout")
        self.prefix_combo = QComboBox(ImportLogin)
        self.prefix_combo.setObjectName(u"prefix_combo")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.prefix_combo.sizePolicy().hasHeightForWidth())
        self.prefix_combo.setSizePolicy(sizePolicy1)
        self.prefix_combo.setEditable(True)

        self.prefix_layout.addWidget(self.prefix_combo)

        self.prefix_button = QPushButton(ImportLogin)
        self.prefix_button.setObjectName(u"prefix_button")

        self.prefix_layout.addWidget(self.prefix_button)

        self.prefix_layout.setStretch(0, 1)

        self.form_layout.setLayout(0, QFormLayout.ItemRole.FieldRole, self.prefix_layout)

        self.prefix_label = QLabel(ImportLogin)
        self.prefix_label.setObjectName(u"prefix_label")

        self.form_layout.setWidget(0, QFormLayout.LabelRole, self.prefix_label)

        self.status_label = QLabel(ImportLogin)
        self.status_label.setObjectName(u"status_label")
        font1 = QFont()
        font1.setItalic(True)
        self.status_label.setFont(font1)
        self.status_label.setText(u"")

        self.form_layout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.status_label)


        self.main_layout.addLayout(self.form_layout)

        self.vspacer = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.main_layout.addItem(self.vspacer)

        self.info_label = QLabel(ImportLogin)
        self.info_label.setObjectName(u"info_label")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.info_label.sizePolicy().hasHeightForWidth())
        self.info_label.setSizePolicy(sizePolicy2)
        self.info_label.setWordWrap(True)

        self.main_layout.addWidget(self.info_label)


        self.retranslateUi(ImportLogin)
    # setupUi

    def retranslateUi(self, ImportLogin):
        self.title_label.setText(QCoreApplication.translate("ImportLogin", u"Import existing session from EGL", None))
        self.prefix_button.setText(QCoreApplication.translate("ImportLogin", u"Browse...", None))
        self.prefix_label.setText(QCoreApplication.translate("ImportLogin", u"Select prefix", None))
        self.info_label.setText(QCoreApplication.translate("ImportLogin", u"<i>Please select the Wine prefix where Epic Games Launcher is installed. You will get logged out from EGL in the process.</i>", None))
        pass
    # retranslateUi


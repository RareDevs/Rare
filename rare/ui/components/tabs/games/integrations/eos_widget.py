# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'eos_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QLayout, QPushButton, QSizePolicy,
    QStackedWidget, QVBoxLayout, QWidget)

class Ui_EosWidget(object):
    def setupUi(self, EosWidget):
        if not EosWidget.objectName():
            EosWidget.setObjectName(u"EosWidget")
        EosWidget.resize(465, 98)
        EosWidget.setWindowTitle(u"GroupBox")
        self.eos_layout = QVBoxLayout(EosWidget)
        self.eos_layout.setObjectName(u"eos_layout")
        self.eos_layout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.overlay_stack = QStackedWidget(EosWidget)
        self.overlay_stack.setObjectName(u"overlay_stack")
        self.install_page = QWidget()
        self.install_page.setObjectName(u"install_page")
        self.install_page_layout = QHBoxLayout(self.install_page)
        self.install_page_layout.setObjectName(u"install_page_layout")
        self.install_page_layout.setContentsMargins(0, 0, 0, 0)
        self.install_label_layout = QFormLayout()
        self.install_label_layout.setObjectName(u"install_label_layout")
        self.install_label_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTop|Qt.AlignTrailing)
        self.install_label_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.install_label = QLabel(self.install_page)
        self.install_label.setObjectName(u"install_label")

        self.install_label_layout.setWidget(0, QFormLayout.LabelRole, self.install_label)

        self.install_text = QLabel(self.install_page)
        self.install_text.setObjectName(u"install_text")

        self.install_label_layout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.install_text)


        self.install_page_layout.addLayout(self.install_label_layout)

        self.install_button_layout = QVBoxLayout()
        self.install_button_layout.setObjectName(u"install_button_layout")
        self.install_button_layout.setContentsMargins(-1, -1, 0, -1)
        self.install_button = QPushButton(self.install_page)
        self.install_button.setObjectName(u"install_button")
        self.install_button.setMinimumSize(QSize(140, 0))

        self.install_button_layout.addWidget(self.install_button, 0, Qt.AlignmentFlag.AlignTop)


        self.install_page_layout.addLayout(self.install_button_layout)

        self.install_page_layout.setStretch(0, 1)
        self.overlay_stack.addWidget(self.install_page)
        self.info_page = QWidget()
        self.info_page.setObjectName(u"info_page")
        self.info_page_layout = QHBoxLayout(self.info_page)
        self.info_page_layout.setObjectName(u"info_page_layout")
        self.info_page_layout.setContentsMargins(0, 0, 0, 0)
        self.info_label_layout = QFormLayout()
        self.info_label_layout.setObjectName(u"info_label_layout")
        self.info_label_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTop|Qt.AlignTrailing)
        self.info_label_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.version_label = QLabel(self.info_page)
        self.version_label.setObjectName(u"version_label")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.info_label_layout.setWidget(0, QFormLayout.LabelRole, self.version_label)

        self.path_label = QLabel(self.info_page)
        self.path_label.setObjectName(u"path_label")
        self.path_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.info_label_layout.setWidget(1, QFormLayout.LabelRole, self.path_label)


        self.info_page_layout.addLayout(self.info_label_layout)

        self.info_button_layout = QVBoxLayout()
        self.info_button_layout.setObjectName(u"info_button_layout")
        self.update_button = QPushButton(self.info_page)
        self.update_button.setObjectName(u"update_button")
        self.update_button.setMinimumSize(QSize(140, 0))

        self.info_button_layout.addWidget(self.update_button, 0, Qt.AlignmentFlag.AlignTop)

        self.uninstall_button = QPushButton(self.info_page)
        self.uninstall_button.setObjectName(u"uninstall_button")
        self.uninstall_button.setMinimumSize(QSize(140, 0))

        self.info_button_layout.addWidget(self.uninstall_button, 0, Qt.AlignmentFlag.AlignTop)


        self.info_page_layout.addLayout(self.info_button_layout)

        self.info_page_layout.setStretch(0, 1)
        self.overlay_stack.addWidget(self.info_page)

        self.eos_layout.addWidget(self.overlay_stack)


        self.retranslateUi(EosWidget)

        self.overlay_stack.setCurrentIndex(0)

    # setupUi

    def retranslateUi(self, EosWidget):
        EosWidget.setTitle(QCoreApplication.translate("EosWidget", u"Epic Overlay", None))
        self.install_label.setText(QCoreApplication.translate("EosWidget", u"Version", None))
        self.install_text.setText(QCoreApplication.translate("EosWidget", u"Epic Online Services Overlay is not installed", None))
        self.install_button.setText(QCoreApplication.translate("EosWidget", u"Install", None))
        self.version_label.setText(QCoreApplication.translate("EosWidget", u"Version", None))
        self.path_label.setText(QCoreApplication.translate("EosWidget", u"Install folder", None))
        self.update_button.setText(QCoreApplication.translate("EosWidget", u"Update", None))
        self.uninstall_button.setText(QCoreApplication.translate("EosWidget", u"Uninstall", None))
    # retranslateUi


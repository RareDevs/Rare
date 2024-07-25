# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'egl_sync_list_group.ui'
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
from PySide6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_EGLSyncListGroup(object):
    def setupUi(self, EGLSyncListGroup):
        if not EGLSyncListGroup.objectName():
            EGLSyncListGroup.setObjectName(u"EGLSyncListGroup")
        EGLSyncListGroup.resize(461, 206)
        EGLSyncListGroup.setWindowTitle(u"EGLSyncListGroup")
        EGLSyncListGroup.setTitle(u"")
        self.egl_sync_list_layout = QVBoxLayout(EGLSyncListGroup)
        self.egl_sync_list_layout.setObjectName(u"egl_sync_list_layout")
        self.label = QLabel(EGLSyncListGroup)
        self.label.setObjectName(u"label")
        self.label.setText(u"")

        self.egl_sync_list_layout.addWidget(self.label)

        self.list = QListWidget(EGLSyncListGroup)
        self.list.setObjectName(u"list")
        self.list.setAlternatingRowColors(True)
        self.list.setSpacing(1)
        self.list.setSortingEnabled(True)

        self.egl_sync_list_layout.addWidget(self.list)

        self.buttons_widget = QWidget(EGLSyncListGroup)
        self.buttons_widget.setObjectName(u"buttons_widget")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttons_widget.sizePolicy().hasHeightForWidth())
        self.buttons_widget.setSizePolicy(sizePolicy)
        self.buttons_layout = QHBoxLayout(self.buttons_widget)
        self.buttons_layout.setObjectName(u"buttons_layout")
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.select_all_button = QPushButton(self.buttons_widget)
        self.select_all_button.setObjectName(u"select_all_button")

        self.buttons_layout.addWidget(self.select_all_button)

        self.select_none_button = QPushButton(self.buttons_widget)
        self.select_none_button.setObjectName(u"select_none_button")

        self.buttons_layout.addWidget(self.select_none_button)

        self.buttons_hspacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.buttons_layout.addItem(self.buttons_hspacer)

        self.action_button = QPushButton(self.buttons_widget)
        self.action_button.setObjectName(u"action_button")
        self.action_button.setText(u"Action")

        self.buttons_layout.addWidget(self.action_button)


        self.egl_sync_list_layout.addWidget(self.buttons_widget)


        self.retranslateUi(EGLSyncListGroup)
    # setupUi

    def retranslateUi(self, EGLSyncListGroup):
        self.select_all_button.setText(QCoreApplication.translate("EGLSyncListGroup", u"Select all", None))
        self.select_none_button.setText(QCoreApplication.translate("EGLSyncListGroup", u"Select none", None))
        pass
    # retranslateUi


# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dlcs.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QLayout,
    QSizePolicy, QToolBox, QVBoxLayout, QWidget)

class Ui_GameDlcs(object):
    def setupUi(self, GameDlcs):
        if not GameDlcs.objectName():
            GameDlcs.setObjectName(u"GameDlcs")
        GameDlcs.resize(271, 141)
        GameDlcs.setWindowTitle(u"GameDlcs")
        GameDlcs.setFrameShape(QFrame.Shape.StyledPanel)
        GameDlcs.setFrameShadow(QFrame.Sunken)
        GameDlcs.setLineWidth(0)
        self.installed_dlc_page = QWidget()
        self.installed_dlc_page.setObjectName(u"installed_dlc_page")
        self.installed_dlc_page.setGeometry(QRect(0, 0, 287, 62))
        self.installed_dlc_page_layout = QVBoxLayout(self.installed_dlc_page)
        self.installed_dlc_page_layout.setObjectName(u"installed_dlc_page_layout")
        self.installed_dlc_page_layout.setContentsMargins(0, 0, 0, 0)
        self.installed_dlc_label = QLabel(self.installed_dlc_page)
        self.installed_dlc_label.setObjectName(u"installed_dlc_label")

        self.installed_dlc_page_layout.addWidget(self.installed_dlc_label, 0, Qt.AlignmentFlag.AlignTop)

        self.installed_dlc_container = QWidget(self.installed_dlc_page)
        self.installed_dlc_container.setObjectName(u"installed_dlc_container")
        self.installed_dlc_container_layout = QVBoxLayout(self.installed_dlc_container)
        self.installed_dlc_container_layout.setObjectName(u"installed_dlc_container_layout")
        self.installed_dlc_container_layout.setContentsMargins(0, 0, 3, 0)

        self.installed_dlc_page_layout.addWidget(self.installed_dlc_container, 0, Qt.AlignmentFlag.AlignTop)

        self.installed_dlc_page_layout.setStretch(1, 1)
        GameDlcs.addItem(self.installed_dlc_page, u"Installed DLCs")
        self.available_dlc_page = QWidget()
        self.available_dlc_page.setObjectName(u"available_dlc_page")
        self.available_dlc_page.setGeometry(QRect(0, 0, 271, 83))
        self.available_dlc_page_layou = QVBoxLayout(self.available_dlc_page)
        self.available_dlc_page_layou.setObjectName(u"available_dlc_page_layou")
        self.available_dlc_page_layou.setContentsMargins(0, 0, 0, 0)
        self.available_dlc_label = QLabel(self.available_dlc_page)
        self.available_dlc_label.setObjectName(u"available_dlc_label")

        self.available_dlc_page_layou.addWidget(self.available_dlc_label, 0, Qt.AlignmentFlag.AlignTop)

        self.available_dlc_container = QWidget(self.available_dlc_page)
        self.available_dlc_container.setObjectName(u"available_dlc_container")
        self.available_dlc_container_layout = QVBoxLayout(self.available_dlc_container)
        self.available_dlc_container_layout.setObjectName(u"available_dlc_container_layout")
        self.available_dlc_container_layout.setContentsMargins(0, 0, 3, 0)

        self.available_dlc_page_layou.addWidget(self.available_dlc_container, 0, Qt.AlignmentFlag.AlignTop)

        self.available_dlc_page_layou.setStretch(1, 1)
        GameDlcs.addItem(self.available_dlc_page, u"Available DLCs")

        self.retranslateUi(GameDlcs)
    # setupUi

    def retranslateUi(self, GameDlcs):
        self.installed_dlc_label.setText(QCoreApplication.translate("GameDlcs", u"No Downloadable Content has been installed.", None))
        GameDlcs.setItemText(GameDlcs.indexOf(self.installed_dlc_page), QCoreApplication.translate("GameDlcs", u"Installed DLCs", None))
        self.available_dlc_label.setText(QCoreApplication.translate("GameDlcs", u"No Downloadable Content is available", None))
        GameDlcs.setItemText(GameDlcs.indexOf(self.available_dlc_page), QCoreApplication.translate("GameDlcs", u"Available DLCs", None))
        pass
    # retranslateUi


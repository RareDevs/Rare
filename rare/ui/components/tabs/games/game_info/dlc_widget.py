# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dlc_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QWidget)

class Ui_GameDlcWidget(object):
    def setupUi(self, GameDlcWidget):
        if not GameDlcWidget.objectName():
            GameDlcWidget.setObjectName(u"GameDlcWidget")
        GameDlcWidget.resize(454, 58)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(GameDlcWidget.sizePolicy().hasHeightForWidth())
        GameDlcWidget.setSizePolicy(sizePolicy)
        GameDlcWidget.setWindowTitle(u"GameDlcWidget")
        GameDlcWidget.setFrameShape(QFrame.Shape.StyledPanel)
        GameDlcWidget.setFrameShadow(QFrame.Shadow.Plain)
        self.dlc_layout = QHBoxLayout(GameDlcWidget)
        self.dlc_layout.setObjectName(u"dlc_layout")
        self.dlc_layout.setContentsMargins(0, 0, 0, 0)
        self.dlc_info = QWidget(GameDlcWidget)
        self.dlc_info.setObjectName(u"dlc_info")
        self.dlc_info_layout = QFormLayout(self.dlc_info)
        self.dlc_info_layout.setObjectName(u"dlc_info_layout")
        self.dlc_info_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.dlc_info_layout.setContentsMargins(0, 0, 0, 0)
        self.dlc_name_label = QLabel(self.dlc_info)
        self.dlc_name_label.setObjectName(u"dlc_name_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.dlc_name_label.sizePolicy().hasHeightForWidth())
        self.dlc_name_label.setSizePolicy(sizePolicy1)
        font = QFont()
        font.setBold(True)
        self.dlc_name_label.setFont(font)

        self.dlc_info_layout.setWidget(0, QFormLayout.LabelRole, self.dlc_name_label)

        self.dlc_name = QLabel(self.dlc_info)
        self.dlc_name.setObjectName(u"dlc_name")
        self.dlc_name.setMinimumSize(QSize(160, 0))
        self.dlc_name.setText(u"dlc_name")
        self.dlc_name.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.dlc_info_layout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.dlc_name)

        self.version_label = QLabel(self.dlc_info)
        self.version_label.setObjectName(u"version_label")
        sizePolicy1.setHeightForWidth(self.version_label.sizePolicy().hasHeightForWidth())
        self.version_label.setSizePolicy(sizePolicy1)
        self.version_label.setFont(font)

        self.dlc_info_layout.setWidget(1, QFormLayout.LabelRole, self.version_label)

        self.version = QLabel(self.dlc_info)
        self.version.setObjectName(u"version")
        self.version.setMinimumSize(QSize(160, 0))
        self.version.setText(u"version")
        self.version.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.dlc_info_layout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.version)

        self.app_name_label = QLabel(self.dlc_info)
        self.app_name_label.setObjectName(u"app_name_label")
        sizePolicy1.setHeightForWidth(self.app_name_label.sizePolicy().hasHeightForWidth())
        self.app_name_label.setSizePolicy(sizePolicy1)
        self.app_name_label.setFont(font)

        self.dlc_info_layout.setWidget(2, QFormLayout.LabelRole, self.app_name_label)

        self.app_name = QLabel(self.dlc_info)
        self.app_name.setObjectName(u"app_name")
        self.app_name.setMinimumSize(QSize(160, 0))
        self.app_name.setText(u"app_name")
        self.app_name.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.dlc_info_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.app_name)


        self.dlc_layout.addWidget(self.dlc_info)

        self.hspacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.dlc_layout.addItem(self.hspacer)

        self.action_button = QPushButton(GameDlcWidget)
        self.action_button.setObjectName(u"action_button")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.action_button.sizePolicy().hasHeightForWidth())
        self.action_button.setSizePolicy(sizePolicy2)
        self.action_button.setMinimumSize(QSize(160, 0))
        self.action_button.setText(u"Action")

        self.dlc_layout.addWidget(self.action_button, 0, Qt.AlignmentFlag.AlignBottom)

        self.dlc_layout.setStretch(1, 1)

        self.retranslateUi(GameDlcWidget)
    # setupUi

    def retranslateUi(self, GameDlcWidget):
        self.dlc_name_label.setText(QCoreApplication.translate("GameDlcWidget", u"DLC Name", None))
        self.version_label.setText(QCoreApplication.translate("GameDlcWidget", u"Version", None))
        self.app_name_label.setText(QCoreApplication.translate("GameDlcWidget", u"Application", None))
        pass
    # retranslateUi


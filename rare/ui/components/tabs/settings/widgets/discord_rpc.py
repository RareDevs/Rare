# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'discord_rpc.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout,
    QGroupBox, QLabel, QSizePolicy, QWidget)

class Ui_DiscordRPCSettings(object):
    def setupUi(self, DiscordRPCSettings):
        if not DiscordRPCSettings.objectName():
            DiscordRPCSettings.setObjectName(u"DiscordRPCSettings")
        DiscordRPCSettings.resize(370, 149)
        DiscordRPCSettings.setWindowTitle(u"DiscordRPCSettings")
        self.main_layout = QGridLayout(DiscordRPCSettings)
        self.main_layout.setObjectName(u"main_layout")
        self.enable = QComboBox(DiscordRPCSettings)
        self.enable.addItem("")
        self.enable.addItem("")
        self.enable.addItem("")
        self.enable.setObjectName(u"enable")

        self.main_layout.addWidget(self.enable, 0, 1, 1, 1)

        self.label = QLabel(DiscordRPCSettings)
        self.label.setObjectName(u"label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)

        self.main_layout.addWidget(self.label, 0, 0, 1, 1)

        self.show_game = QCheckBox(DiscordRPCSettings)
        self.show_game.setObjectName(u"show_game")

        self.main_layout.addWidget(self.show_game, 1, 0, 1, 2)

        self.show_os = QCheckBox(DiscordRPCSettings)
        self.show_os.setObjectName(u"show_os")

        self.main_layout.addWidget(self.show_os, 2, 0, 1, 2)

        self.show_time = QCheckBox(DiscordRPCSettings)
        self.show_time.setObjectName(u"show_time")

        self.main_layout.addWidget(self.show_time, 3, 0, 1, 2)


        self.retranslateUi(DiscordRPCSettings)
    # setupUi

    def retranslateUi(self, DiscordRPCSettings):
        DiscordRPCSettings.setTitle(QCoreApplication.translate("DiscordRPCSettings", u"Discord RPC", None))
        self.enable.setItemText(0, QCoreApplication.translate("DiscordRPCSettings", u"When Playing", None))
        self.enable.setItemText(1, QCoreApplication.translate("DiscordRPCSettings", u"Always", None))
        self.enable.setItemText(2, QCoreApplication.translate("DiscordRPCSettings", u"Never", None))

        self.label.setText(QCoreApplication.translate("DiscordRPCSettings", u"Show", None))
        self.show_game.setText(QCoreApplication.translate("DiscordRPCSettings", u"Show Game", None))
        self.show_os.setText(QCoreApplication.translate("DiscordRPCSettings", u"Show OS", None))
        self.show_time.setText(QCoreApplication.translate("DiscordRPCSettings", u"Show Time playing", None))
    # retranslateUi


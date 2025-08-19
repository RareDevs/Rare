# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'discord_rpc.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication)
from PySide6.QtWidgets import (QCheckBox, QComboBox, QGridLayout,
    QLabel, QSizePolicy)

class Ui_DiscordRPCSettings(object):
    def setupUi(self, DiscordRPCSettings):
        if not DiscordRPCSettings.objectName():
            DiscordRPCSettings.setObjectName(u"DiscordRPCSettings")
        DiscordRPCSettings.resize(370, 149)
        DiscordRPCSettings.setWindowTitle(u"DiscordRPCSettings")
        self.main_layout = QGridLayout(DiscordRPCSettings)
        self.main_layout.setObjectName(u"main_layout")
        self.mode_combo = QComboBox(DiscordRPCSettings)
        self.mode_combo.setObjectName(u"mode_combo")

        self.main_layout.addWidget(self.mode_combo, 0, 1, 1, 1)

        self.label = QLabel(DiscordRPCSettings)
        self.label.setObjectName(u"label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)

        self.main_layout.addWidget(self.label, 0, 0, 1, 1)

        self.game_check = QCheckBox(DiscordRPCSettings)
        self.game_check.setObjectName(u"game_check")

        self.main_layout.addWidget(self.game_check, 1, 0, 1, 2)

        self.os_check = QCheckBox(DiscordRPCSettings)
        self.os_check.setObjectName(u"os_check")

        self.main_layout.addWidget(self.os_check, 2, 0, 1, 2)

        self.time_check = QCheckBox(DiscordRPCSettings)
        self.time_check.setObjectName(u"time_check")

        self.main_layout.addWidget(self.time_check, 3, 0, 1, 2)


        self.retranslateUi(DiscordRPCSettings)
    # setupUi

    def retranslateUi(self, DiscordRPCSettings):
        DiscordRPCSettings.setTitle(QCoreApplication.translate("DiscordRPCSettings", u"Discord RPC", None))
        self.label.setText(QCoreApplication.translate("DiscordRPCSettings", u"Show", None))
        self.game_check.setText(QCoreApplication.translate("DiscordRPCSettings", u"Show game", None))
        self.os_check.setText(QCoreApplication.translate("DiscordRPCSettings", u"Show OS", None))
        self.time_check.setText(QCoreApplication.translate("DiscordRPCSettings", u"Show play time", None))
    # retranslateUi


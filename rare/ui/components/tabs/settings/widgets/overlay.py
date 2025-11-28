# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'overlay.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QLabel, QSizePolicy, QSpacerItem


class Ui_OverlaySettings(object):
    def setupUi(self, OverlaySettings):
        if not OverlaySettings.objectName():
            OverlaySettings.setObjectName(u"OverlaySettings")
        OverlaySettings.resize(343, 119)
        OverlaySettings.setWindowTitle(u"OverlaySettings")
        OverlaySettings.setTitle(u"")
        self.main_layout = QFormLayout(OverlaySettings)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.overlay_state_label = QLabel(OverlaySettings)
        self.overlay_state_label.setObjectName(u"overlay_state_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.overlay_state_label.sizePolicy().hasHeightForWidth())
        self.overlay_state_label.setSizePolicy(sizePolicy)
        self.overlay_state_label.setText(u"error")

        self.main_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.overlay_state_label)

        self.overlay_state_combo = QComboBox(OverlaySettings)
        self.overlay_state_combo.setObjectName(u"overlay_state_combo")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.overlay_state_combo.sizePolicy().hasHeightForWidth())
        self.overlay_state_combo.setSizePolicy(sizePolicy1)

        self.main_layout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.overlay_state_combo)

        self.current_value_label = QLabel(OverlaySettings)
        self.current_value_label.setObjectName(u"current_value_label")

        self.main_layout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.current_value_label)

        self.current_value_info = QLabel(OverlaySettings)
        self.current_value_info.setObjectName(u"current_value_info")
        self.current_value_info.setMinimumSize(QSize(1, 0))
        font = QFont()
        self.current_value_info.setFont(font)
        self.current_value_info.setFrameShape(QFrame.Shape.StyledPanel)
        self.current_value_info.setFrameShadow(QFrame.Shadow.Sunken)
        self.current_value_info.setText(u"")
        self.current_value_info.setTextFormat(Qt.TextFormat.PlainText)
        self.current_value_info.setWordWrap(True)
        self.current_value_info.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.main_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.current_value_info)

        self.options_group = QGroupBox(OverlaySettings)
        self.options_group.setObjectName(u"options_group")
        self.options_group.setTitle(u"")
        self.options_layout = QGridLayout(self.options_group)
        self.options_layout.setObjectName(u"options_layout")
        self.options_form = QFormLayout()
        self.options_form.setObjectName(u"options_form")
        self.options_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.options_layout.addLayout(self.options_form, 1, 0, 1, 1)

        self.options_grid = QGridLayout()
        self.options_grid.setObjectName(u"options_grid")

        self.options_layout.addLayout(self.options_grid, 0, 0, 1, 1)

        self.hspacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.options_layout.addItem(self.hspacer, 0, 1, 2, 1)


        self.main_layout.setWidget(1, QFormLayout.ItemRole.SpanningRole, self.options_group)


        self.retranslateUi(OverlaySettings)
    # setupUi

    def retranslateUi(self, OverlaySettings):
        self.current_value_label.setText(QCoreApplication.translate("OverlaySettings", u"Current", None))
        pass
    # retranslateUi


# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'move_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, Qt)
from PySide6.QtGui import (QFont)
from PySide6.QtWidgets import (QFormLayout, QFrame, QLabel)

class Ui_MoveDialog(object):
    def setupUi(self, MoveDialog):
        if not MoveDialog.objectName():
            MoveDialog.setObjectName(u"MoveDialog")
        MoveDialog.resize(148, 85)
        MoveDialog.setWindowTitle(u"MoveDialog")
        self.main_layout = QFormLayout(MoveDialog)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.target_dir_label = QLabel(MoveDialog)
        self.target_dir_label.setObjectName(u"target_dir_label")

        self.main_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.target_dir_label)

        self.required_space_label = QLabel(MoveDialog)
        self.required_space_label.setObjectName(u"required_space_label")

        self.main_layout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.required_space_label)

        self.available_space_label = QLabel(MoveDialog)
        self.available_space_label.setObjectName(u"available_space_label")

        self.main_layout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.available_space_label)

        self.required_space_text = QLabel(MoveDialog)
        self.required_space_text.setObjectName(u"required_space_text")
        font = QFont()
        font.setBold(True)
        self.required_space_text.setFont(font)
        self.required_space_text.setText(u"")

        self.main_layout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.required_space_text)

        self.available_space_text = QLabel(MoveDialog)
        self.available_space_text.setObjectName(u"available_space_text")
        self.available_space_text.setFont(font)
        self.available_space_text.setText(u"")

        self.main_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.available_space_text)

        self.warning_label = QLabel(MoveDialog)
        self.warning_label.setObjectName(u"warning_label")

        self.main_layout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.warning_label)

        self.warning_text = QLabel(MoveDialog)
        self.warning_text.setObjectName(u"warning_text")
        font1 = QFont()
        font1.setItalic(True)
        self.warning_text.setFont(font1)
        self.warning_text.setFrameShape(QFrame.Shape.StyledPanel)
        self.warning_text.setFrameShadow(QFrame.Shadow.Sunken)
        self.warning_text.setText(u"None")
        self.warning_text.setWordWrap(True)
        self.warning_text.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.main_layout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.warning_text)


        self.retranslateUi(MoveDialog)
    # setupUi

    def retranslateUi(self, MoveDialog):
        self.target_dir_label.setText(QCoreApplication.translate("MoveDialog", u"Target folder", None))
        self.required_space_label.setText(QCoreApplication.translate("MoveDialog", u"Required space", None))
        self.available_space_label.setText(QCoreApplication.translate("MoveDialog", u"Available space", None))
        self.warning_label.setText(QCoreApplication.translate("MoveDialog", u"Warning", None))
        pass
    # retranslateUi


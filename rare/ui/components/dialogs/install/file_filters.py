# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'file_filters.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
)


class Ui_InstallDialogFileFilters(object):
    def setupUi(self, InstallDialogFileFilters):
        if not InstallDialogFileFilters.objectName():
            InstallDialogFileFilters.setObjectName(u"InstallDialogFileFilters")
        InstallDialogFileFilters.resize(274, 246)
        InstallDialogFileFilters.setWindowTitle(u"InstallDialogFileFilters")
        self.main_layout = QFormLayout(InstallDialogFileFilters)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.exclude_prefix_label = QLabel(InstallDialogFileFilters)
        self.exclude_prefix_label.setObjectName(u"exclude_prefix_label")

        self.main_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.exclude_prefix_label)

        self.exclude_prefix_layout = QHBoxLayout()
        self.exclude_prefix_layout.setObjectName(u"exclude_prefix_layout")
        self.exclude_prefix_info = QLabel(InstallDialogFileFilters)
        self.exclude_prefix_info.setObjectName(u"exclude_prefix_info")
        self.exclude_prefix_info.setFrameShape(QFrame.Shape.StyledPanel)
        self.exclude_prefix_info.setFrameShadow(QFrame.Shadow.Sunken)
        self.exclude_prefix_info.setWordWrap(True)

        self.exclude_prefix_layout.addWidget(self.exclude_prefix_info)

        self.exclude_prefix_button = QPushButton(InstallDialogFileFilters)
        self.exclude_prefix_button.setObjectName(u"exclude_prefix_button")

        self.exclude_prefix_layout.addWidget(self.exclude_prefix_button)

        self.exclude_prefix_layout.setStretch(0, 1)

        self.main_layout.setLayout(0, QFormLayout.ItemRole.FieldRole, self.exclude_prefix_layout)

        self.exclude_list = QListWidget(InstallDialogFileFilters)
        self.exclude_list.setObjectName(u"exclude_list")

        self.main_layout.setWidget(1, QFormLayout.ItemRole.SpanningRole, self.exclude_list)


        self.retranslateUi(InstallDialogFileFilters)
    # setupUi

    def retranslateUi(self, InstallDialogFileFilters):
        self.exclude_prefix_label.setText(QCoreApplication.translate("InstallDialogFileFilters", u"Excluded files", None))
        self.exclude_prefix_info.setText("")
        self.exclude_prefix_button.setText(QCoreApplication.translate("InstallDialogFileFilters", u"Select...", None))
        pass
    # retranslateUi


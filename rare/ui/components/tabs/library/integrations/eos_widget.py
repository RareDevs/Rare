# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'eos_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QSize, Qt)
from PySide6.QtWidgets import (QFormLayout, QHBoxLayout,
    QLabel, QLayout, QPushButton, QStackedWidget, QVBoxLayout, QWidget)

class Ui_EosWidget(object):
    def setupUi(self, EosWidget):
        if not EosWidget.objectName():
            EosWidget.setObjectName(u"EosWidget")
        EosWidget.resize(528, 95)
        EosWidget.setWindowTitle(u"GroupBox")
        self.eos_layout = QVBoxLayout(EosWidget)
        self.eos_layout.setObjectName(u"eos_layout")
        self.eos_layout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.overlay_widget = QWidget(EosWidget)
        self.overlay_widget.setObjectName(u"overlay_widget")
        self.overlay_widget_layout = QHBoxLayout(self.overlay_widget)
        self.overlay_widget_layout.setObjectName(u"overlay_widget_layout")
        self.overlay_widget_layout.setContentsMargins(0, 0, 0, 0)
        self.info_layout = QFormLayout()
        self.info_layout.setObjectName(u"info_layout")
        self.info_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignTrailing)
        self.info_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.version_label = QLabel(self.overlay_widget)
        self.version_label.setObjectName(u"version_label")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.info_layout.setWidget(0, QFormLayout.LabelRole, self.version_label)

        self.path_label = QLabel(self.overlay_widget)
        self.path_label.setObjectName(u"path_label")
        self.path_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.info_layout.setWidget(1, QFormLayout.LabelRole, self.path_label)


        self.overlay_widget_layout.addLayout(self.info_layout)

        self.button_stack = QStackedWidget(self.overlay_widget)
        self.button_stack.setObjectName(u"button_stack")
        self.install_page = QWidget()
        self.install_page.setObjectName(u"install_page")
        self.install_page_layout = QHBoxLayout(self.install_page)
        self.install_page_layout.setObjectName(u"install_page_layout")
        self.install_page_layout.setContentsMargins(0, 0, 0, 0)
        self.install_button = QPushButton(self.install_page)
        self.install_button.setObjectName(u"install_button")
        self.install_button.setMinimumSize(QSize(140, 26))

        self.install_page_layout.addWidget(self.install_button, 0, Qt.AlignmentFlag.AlignBottom)

        self.button_stack.addWidget(self.install_page)
        self.update_page = QWidget()
        self.update_page.setObjectName(u"update_page")
        self.update_page_layout = QVBoxLayout(self.update_page)
        self.update_page_layout.setObjectName(u"update_page_layout")
        self.update_page_layout.setContentsMargins(0, 0, 0, 0)
        self.update_button = QPushButton(self.update_page)
        self.update_button.setObjectName(u"update_button")
        self.update_button.setMinimumSize(QSize(140, 26))

        self.update_page_layout.addWidget(self.update_button, 0, Qt.AlignmentFlag.AlignBottom)

        self.uninstall_button = QPushButton(self.update_page)
        self.uninstall_button.setObjectName(u"uninstall_button")
        self.uninstall_button.setMinimumSize(QSize(140, 26))

        self.update_page_layout.addWidget(self.uninstall_button, 0, Qt.AlignmentFlag.AlignBottom)

        self.button_stack.addWidget(self.update_page)

        self.overlay_widget_layout.addWidget(self.button_stack, 0, Qt.AlignmentFlag.AlignTop)

        self.overlay_widget_layout.setStretch(0, 1)

        self.eos_layout.addWidget(self.overlay_widget, 0, Qt.AlignmentFlag.AlignTop)


        self.retranslateUi(EosWidget)

        self.button_stack.setCurrentIndex(0)

    # setupUi

    def retranslateUi(self, EosWidget):
        EosWidget.setTitle(QCoreApplication.translate("EosWidget", u"Epic Overlay", None))
        self.version_label.setText(QCoreApplication.translate("EosWidget", u"Version", None))
        self.path_label.setText(QCoreApplication.translate("EosWidget", u"Install folder", None))
        self.install_button.setText(QCoreApplication.translate("EosWidget", u"Install", None))
        self.update_button.setText(QCoreApplication.translate("EosWidget", u"Update", None))
        self.uninstall_button.setText(QCoreApplication.translate("EosWidget", u"Uninstall", None))
    # retranslateUi


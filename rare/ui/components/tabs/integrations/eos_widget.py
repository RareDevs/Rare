
################################################################################
## Form generated from reading UI file 'eos_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QSize, Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class Ui_EosWidget:
    def setupUi(self, EosWidget):
        if not EosWidget.objectName():
            EosWidget.setObjectName("EosWidget")
        EosWidget.resize(245, 95)
        EosWidget.setWindowTitle("GroupBox")
        self.eos_layout = QVBoxLayout(EosWidget)
        self.eos_layout.setObjectName("eos_layout")
        self.eos_layout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.overlay_widget = QWidget(EosWidget)
        self.overlay_widget.setObjectName("overlay_widget")
        self.overlay_widget_layout = QHBoxLayout(self.overlay_widget)
        self.overlay_widget_layout.setObjectName("overlay_widget_layout")
        self.overlay_widget_layout.setContentsMargins(0, 0, 0, 0)
        self.info_layout = QFormLayout()
        self.info_layout.setObjectName("info_layout")
        self.info_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignTrailing)
        self.info_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.version_label = QLabel(self.overlay_widget)
        self.version_label.setObjectName("version_label")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.info_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.version_label)

        self.path_label = QLabel(self.overlay_widget)
        self.path_label.setObjectName("path_label")
        self.path_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.info_layout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.path_label)


        self.overlay_widget_layout.addLayout(self.info_layout)

        self.button_stack = QStackedWidget(self.overlay_widget)
        self.button_stack.setObjectName("button_stack")
        self.install_page = QWidget()
        self.install_page.setObjectName("install_page")
        self.install_page_layout = QHBoxLayout(self.install_page)
        self.install_page_layout.setObjectName("install_page_layout")
        self.install_page_layout.setContentsMargins(0, 0, 0, 0)
        self.install_button = QPushButton(self.install_page)
        self.install_button.setObjectName("install_button")
        self.install_button.setMinimumSize(QSize(140, 0))

        self.install_page_layout.addWidget(self.install_button)

        self.button_stack.addWidget(self.install_page)
        self.update_page = QWidget()
        self.update_page.setObjectName("update_page")
        self.update_page_layout = QVBoxLayout(self.update_page)
        self.update_page_layout.setObjectName("update_page_layout")
        self.update_page_layout.setContentsMargins(0, 0, 0, 0)
        self.update_button = QPushButton(self.update_page)
        self.update_button.setObjectName("update_button")
        self.update_button.setMinimumSize(QSize(140, 0))

        self.update_page_layout.addWidget(self.update_button)

        self.uninstall_button = QPushButton(self.update_page)
        self.uninstall_button.setObjectName("uninstall_button")
        self.uninstall_button.setMinimumSize(QSize(140, 0))

        self.update_page_layout.addWidget(self.uninstall_button)

        self.button_stack.addWidget(self.update_page)

        self.overlay_widget_layout.addWidget(self.button_stack)

        self.overlay_widget_layout.setStretch(0, 1)

        self.eos_layout.addWidget(self.overlay_widget, 0, Qt.AlignmentFlag.AlignTop)


        self.retranslateUi(EosWidget)

        self.button_stack.setCurrentIndex(0)

    # setupUi

    def retranslateUi(self, EosWidget):
        EosWidget.setTitle(QCoreApplication.translate("EosWidget", "Epic Overlay", None))
        self.version_label.setText(QCoreApplication.translate("EosWidget", "Version", None))
        self.path_label.setText(QCoreApplication.translate("EosWidget", "Install folder", None))
        self.install_button.setText(QCoreApplication.translate("EosWidget", "Install", None))
        self.update_button.setText(QCoreApplication.translate("EosWidget", "Update", None))
        self.uninstall_button.setText(QCoreApplication.translate("EosWidget", "Uninstall", None))
    # retranslateUi


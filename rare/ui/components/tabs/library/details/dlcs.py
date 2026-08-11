
################################################################################
## Form generated from reading UI file 'dlcs.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QRect, Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class Ui_GameDlcs:
    def setupUi(self, GameDlcs):
        if not GameDlcs.objectName():
            GameDlcs.setObjectName("GameDlcs")
        GameDlcs.resize(271, 141)
        GameDlcs.setWindowTitle("GameDlcs")
        GameDlcs.setFrameShape(QFrame.StyledPanel)
        GameDlcs.setFrameShadow(QFrame.Sunken)
        GameDlcs.setLineWidth(0)
        self.installed_dlc_page = QWidget()
        self.installed_dlc_page.setObjectName("installed_dlc_page")
        self.installed_dlc_page.setGeometry(QRect(0, 0, 287, 62))
        self.installed_dlc_page_layout = QVBoxLayout(self.installed_dlc_page)
        self.installed_dlc_page_layout.setObjectName("installed_dlc_page_layout")
        self.installed_dlc_page_layout.setContentsMargins(0, 0, 0, 0)
        self.installed_dlc_label = QLabel(self.installed_dlc_page)
        self.installed_dlc_label.setObjectName("installed_dlc_label")

        self.installed_dlc_page_layout.addWidget(self.installed_dlc_label, 0, Qt.AlignTop)

        self.installed_dlc_container = QWidget(self.installed_dlc_page)
        self.installed_dlc_container.setObjectName("installed_dlc_container")
        self.installed_dlc_container_layout = QVBoxLayout(self.installed_dlc_container)
        self.installed_dlc_container_layout.setObjectName("installed_dlc_container_layout")
        self.installed_dlc_container_layout.setContentsMargins(0, 0, 3, 0)

        self.installed_dlc_page_layout.addWidget(self.installed_dlc_container, 0, Qt.AlignTop)

        self.installed_dlc_page_layout.setStretch(1, 1)
        GameDlcs.addItem(self.installed_dlc_page, "Installed DLCs")
        self.available_dlc_page = QWidget()
        self.available_dlc_page.setObjectName("available_dlc_page")
        self.available_dlc_page.setGeometry(QRect(0, 0, 271, 83))
        self.available_dlc_page_layou = QVBoxLayout(self.available_dlc_page)
        self.available_dlc_page_layou.setObjectName("available_dlc_page_layou")
        self.available_dlc_page_layou.setContentsMargins(0, 0, 0, 0)
        self.available_dlc_label = QLabel(self.available_dlc_page)
        self.available_dlc_label.setObjectName("available_dlc_label")

        self.available_dlc_page_layou.addWidget(self.available_dlc_label, 0, Qt.AlignTop)

        self.available_dlc_container = QWidget(self.available_dlc_page)
        self.available_dlc_container.setObjectName("available_dlc_container")
        self.available_dlc_container_layout = QVBoxLayout(self.available_dlc_container)
        self.available_dlc_container_layout.setObjectName("available_dlc_container_layout")
        self.available_dlc_container_layout.setContentsMargins(0, 0, 3, 0)

        self.available_dlc_page_layou.addWidget(self.available_dlc_container, 0, Qt.AlignTop)

        self.available_dlc_page_layou.setStretch(1, 1)
        GameDlcs.addItem(self.available_dlc_page, "Available DLCs")

        self.retranslateUi(GameDlcs)
    # setupUi

    def retranslateUi(self, GameDlcs):
        self.installed_dlc_label.setText(QCoreApplication.translate("GameDlcs", "No Downloadable Content has been installed.", None))
        GameDlcs.setItemText(GameDlcs.indexOf(self.installed_dlc_page), QCoreApplication.translate("GameDlcs", "Installed DLCs", None))
        self.available_dlc_label.setText(QCoreApplication.translate("GameDlcs", "No Downloadable Content is available", None))
        GameDlcs.setItemText(GameDlcs.indexOf(self.available_dlc_page), QCoreApplication.translate("GameDlcs", "Available DLCs", None))
    # retranslateUi


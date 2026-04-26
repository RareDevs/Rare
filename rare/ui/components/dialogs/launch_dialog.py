
################################################################################
## Form generated from reading UI file 'launch_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QProgressBar, QSizePolicy, QVBoxLayout


class Ui_LaunchDialog:
    def setupUi(self, LaunchDialog):
        if not LaunchDialog.objectName():
            LaunchDialog.setObjectName("LaunchDialog")
        LaunchDialog.resize(400, 160)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(LaunchDialog.sizePolicy().hasHeightForWidth())
        LaunchDialog.setSizePolicy(sizePolicy)
        LaunchDialog.setMinimumSize(QSize(400, 160))
        LaunchDialog.setMaximumSize(QSize(400, 160))
        self.launch_layout = QVBoxLayout(LaunchDialog)
        self.launch_layout.setObjectName("launch_layout")
        self.title_label = QLabel(LaunchDialog)
        self.title_label.setObjectName("title_label")

        self.launch_layout.addWidget(self.title_label)

        self.progress_bar = QProgressBar(LaunchDialog)
        self.progress_bar.setObjectName("progress_bar")
        self.progress_bar.setValue(0)

        self.launch_layout.addWidget(self.progress_bar)

        self.info_label = QLabel(LaunchDialog)
        self.info_label.setObjectName("info_label")
        font = QFont()
        font.setItalic(True)
        self.info_label.setFont(font)

        self.launch_layout.addWidget(self.info_label)


        self.retranslateUi(LaunchDialog)
    # setupUi

    def retranslateUi(self, LaunchDialog):
        LaunchDialog.setWindowTitle(QCoreApplication.translate("LaunchDialog", "Launching", None))
        self.title_label.setText(QCoreApplication.translate("LaunchDialog", "<h2>Launching Rare</h2>", None))
        self.info_label.setText(QCoreApplication.translate("LaunchDialog", "Progress might look stuck when launching for the first time.", None))
    # retranslateUi


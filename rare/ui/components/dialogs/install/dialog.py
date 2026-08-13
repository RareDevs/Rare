
################################################################################
## Form generated from reading UI file 'dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QFrame, QLabel, QSizePolicy


class Ui_InstallDialog:
    def setupUi(self, InstallDialog):
        if not InstallDialog.objectName():
            InstallDialog.setObjectName("InstallDialog")
        InstallDialog.resize(438, 204)
        InstallDialog.setWindowTitle("InstallDialog")
        self.main_layout = QFormLayout(InstallDialog)
        self.main_layout.setObjectName("main_layout")
        self.main_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.install_dir_label = QLabel(InstallDialog)
        self.install_dir_label.setObjectName("install_dir_label")

        self.main_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.install_dir_label)

        self.platform_label = QLabel(InstallDialog)
        self.platform_label.setObjectName("platform_label")

        self.main_layout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.platform_label)

        self.platform_combo = QComboBox(InstallDialog)
        self.platform_combo.setObjectName("platform_combo")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.platform_combo.sizePolicy().hasHeightForWidth())
        self.platform_combo.setSizePolicy(sizePolicy)

        self.main_layout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.platform_combo)

        self.eula_label = QLabel(InstallDialog)
        self.eula_label.setObjectName("eula_label")
        self.eula_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.main_layout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.eula_label)

        self.shortcut_label = QLabel(InstallDialog)
        self.shortcut_label.setObjectName("shortcut_label")
        self.shortcut_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.main_layout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.shortcut_label)

        self.shortcut_check = QCheckBox(InstallDialog)
        self.shortcut_check.setObjectName("shortcut_check")
        font = QFont()
        font.setItalic(True)
        self.shortcut_check.setFont(font)

        self.main_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.shortcut_check)

        self.download_size_label = QLabel(InstallDialog)
        self.download_size_label.setObjectName("download_size_label")

        self.main_layout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.download_size_label)

        self.download_size_text = QLabel(InstallDialog)
        self.download_size_text.setObjectName("download_size_text")
        self.download_size_text.setFont(font)

        self.main_layout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.download_size_text)

        self.install_size_label = QLabel(InstallDialog)
        self.install_size_label.setObjectName("install_size_label")

        self.main_layout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.install_size_label)

        self.install_size_text = QLabel(InstallDialog)
        self.install_size_text.setObjectName("install_size_text")
        self.install_size_text.setFont(font)
        self.install_size_text.setWordWrap(True)

        self.main_layout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.install_size_text)

        self.available_space_label = QLabel(InstallDialog)
        self.available_space_label.setObjectName("available_space_label")

        self.main_layout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.available_space_label)

        self.available_space_text = QLabel(InstallDialog)
        self.available_space_text.setObjectName("available_space_text")
        font1 = QFont()
        font1.setBold(True)
        self.available_space_text.setFont(font1)
        self.available_space_text.setText("")

        self.main_layout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.available_space_text)

        self.warning_label = QLabel(InstallDialog)
        self.warning_label.setObjectName("warning_label")

        self.main_layout.setWidget(7, QFormLayout.ItemRole.LabelRole, self.warning_label)

        self.warning_text = QLabel(InstallDialog)
        self.warning_text.setObjectName("warning_text")
        self.warning_text.setFont(font)
        self.warning_text.setFrameShape(QFrame.Shape.StyledPanel)
        self.warning_text.setFrameShadow(QFrame.Shadow.Sunken)
        self.warning_text.setText("None")
        self.warning_text.setWordWrap(True)
        self.warning_text.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.main_layout.setWidget(7, QFormLayout.ItemRole.FieldRole, self.warning_text)


        self.retranslateUi(InstallDialog)
    # setupUi

    def retranslateUi(self, InstallDialog):
        self.install_dir_label.setText(QCoreApplication.translate("InstallDialog", "Install folder", None))
        self.platform_label.setText(QCoreApplication.translate("InstallDialog", "Platform", None))
        self.eula_label.setText(QCoreApplication.translate("InstallDialog", "Accept EULAs", None))
        self.shortcut_label.setText(QCoreApplication.translate("InstallDialog", "Shortcut", None))
        self.shortcut_check.setText(QCoreApplication.translate("InstallDialog", "Create desktop shortcut", None))
        self.download_size_label.setText(QCoreApplication.translate("InstallDialog", "Download size", None))
        self.download_size_text.setText(QCoreApplication.translate("InstallDialog", "Click verify...", None))
        self.install_size_label.setText(QCoreApplication.translate("InstallDialog", "Total install size", None))
        self.install_size_text.setText(QCoreApplication.translate("InstallDialog", "Click verify...", None))
        self.available_space_label.setText(QCoreApplication.translate("InstallDialog", "Available space", None))
        self.warning_label.setText(QCoreApplication.translate("InstallDialog", "Warning", None))
    # retranslateUi



################################################################################
## Form generated from reading UI file 'move_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QCheckBox, QFormLayout, QFrame, QLabel


class Ui_MoveDialog:
    def setupUi(self, MoveDialog):
        if not MoveDialog.objectName():
            MoveDialog.setObjectName("MoveDialog")
        MoveDialog.resize(572, 149)
        MoveDialog.setWindowTitle("MoveDialog")
        self.main_layout = QFormLayout(MoveDialog)
        self.main_layout.setObjectName("main_layout")
        self.main_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.target_path_label = QLabel(MoveDialog)
        self.target_path_label.setObjectName("target_path_label")

        self.main_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.target_path_label)

        self.full_path_label = QLabel(MoveDialog)
        self.full_path_label.setObjectName("full_path_label")
        font = QFont()
        font.setItalic(True)
        self.full_path_label.setFont(font)

        self.main_layout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.full_path_label)

        self.required_space_label = QLabel(MoveDialog)
        self.required_space_label.setObjectName("required_space_label")

        self.main_layout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.required_space_label)

        self.available_space_label = QLabel(MoveDialog)
        self.available_space_label.setObjectName("available_space_label")

        self.main_layout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.available_space_label)

        self.required_space_text = QLabel(MoveDialog)
        self.required_space_text.setObjectName("required_space_text")
        font1 = QFont()
        font1.setBold(True)
        self.required_space_text.setFont(font1)
        self.required_space_text.setText("")

        self.main_layout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.required_space_text)

        self.available_space_text = QLabel(MoveDialog)
        self.available_space_text.setObjectName("available_space_text")
        self.available_space_text.setFont(font1)
        self.available_space_text.setText("")

        self.main_layout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.available_space_text)

        self.warning_label = QLabel(MoveDialog)
        self.warning_label.setObjectName("warning_label")

        self.main_layout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.warning_label)

        self.warning_text = QLabel(MoveDialog)
        self.warning_text.setObjectName("warning_text")
        self.warning_text.setFont(font)
        self.warning_text.setFrameShape(QFrame.Shape.StyledPanel)
        self.warning_text.setFrameShadow(QFrame.Shadow.Sunken)
        self.warning_text.setText("None")
        self.warning_text.setWordWrap(True)
        self.warning_text.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.main_layout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.warning_text)

        self.rename_path_label = QLabel(MoveDialog)
        self.rename_path_label.setObjectName("rename_path_label")
        self.rename_path_label.setEnabled(True)

        self.main_layout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.rename_path_label)

        self.reset_name_label = QLabel(MoveDialog)
        self.reset_name_label.setObjectName("reset_name_label")

        self.main_layout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.reset_name_label)

        self.reset_name_check = QCheckBox(MoveDialog)
        self.reset_name_check.setObjectName("reset_name_check")
        self.reset_name_check.setEnabled(True)
        self.reset_name_check.setFont(font)

        self.main_layout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.reset_name_check)

        self.rename_path_check = QCheckBox(MoveDialog)
        self.rename_path_check.setObjectName("rename_path_check")
        self.rename_path_check.setEnabled(True)
        self.rename_path_check.setFont(font)

        self.main_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.rename_path_check)


        self.retranslateUi(MoveDialog)
    # setupUi

    def retranslateUi(self, MoveDialog):
        self.target_path_label.setText(QCoreApplication.translate("MoveDialog", "Target folder", None))
        self.full_path_label.setText(QCoreApplication.translate("MoveDialog", "Destination", None))
        self.required_space_label.setText(QCoreApplication.translate("MoveDialog", "Required space", None))
        self.available_space_label.setText(QCoreApplication.translate("MoveDialog", "Available space", None))
        self.warning_label.setText(QCoreApplication.translate("MoveDialog", "Warning", None))
        self.rename_path_label.setText(QCoreApplication.translate("MoveDialog", "Rename folder", None))
        self.reset_name_label.setText(QCoreApplication.translate("MoveDialog", "Reset name", None))
        self.reset_name_check.setText(QCoreApplication.translate("MoveDialog", "Reset the game's install folder name to the default", None))
        self.rename_path_check.setText(QCoreApplication.translate("MoveDialog", "Do not create a sub-directory, use 'target folder' as the game's install folder", None))
    # retranslateUi



################################################################################
## Form generated from reading UI file 'import_group.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy


class Ui_ImportGroup:
    def setupUi(self, ImportGroup):
        if not ImportGroup.objectName():
            ImportGroup.setObjectName("ImportGroup")
        ImportGroup.resize(651, 232)
        ImportGroup.setWindowTitle("ImportGroup")
        ImportGroup.setWindowFilePath("")
        self.import_layout = QFormLayout(ImportGroup)
        self.import_layout.setObjectName("import_layout")
        self.import_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.path_edit_label = QLabel(ImportGroup)
        self.path_edit_label.setObjectName("path_edit_label")

        self.import_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.path_edit_label)

        self.app_name_label = QLabel(ImportGroup)
        self.app_name_label.setObjectName("app_name_label")

        self.import_layout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.app_name_label)

        self.import_folder_label = QLabel(ImportGroup)
        self.import_folder_label.setObjectName("import_folder_label")

        self.import_layout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.import_folder_label)

        self.import_folder_check = QCheckBox(ImportGroup)
        self.import_folder_check.setObjectName("import_folder_check")
        font = QFont()
        font.setItalic(True)
        self.import_folder_check.setFont(font)

        self.import_layout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.import_folder_check)

        self.import_dlcs_label = QLabel(ImportGroup)
        self.import_dlcs_label.setObjectName("import_dlcs_label")

        self.import_layout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.import_dlcs_label)

        self.import_dlcs_check = QCheckBox(ImportGroup)
        self.import_dlcs_check.setObjectName("import_dlcs_check")
        self.import_dlcs_check.setFont(font)

        self.import_layout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.import_dlcs_check)

        self.import_force_label = QLabel(ImportGroup)
        self.import_force_label.setObjectName("import_force_label")

        self.import_layout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.import_force_label)

        self.import_force_check = QCheckBox(ImportGroup)
        self.import_force_check.setObjectName("import_force_check")
        self.import_force_check.setFont(font)

        self.import_layout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.import_force_check)

        self.import_button_label = QLabel(ImportGroup)
        self.import_button_label.setObjectName("import_button_label")
        self.import_button_label.setText("error")

        self.import_layout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.import_button_label)

        self.button_info_layout = QHBoxLayout()
        self.button_info_layout.setObjectName("button_info_layout")
        self.import_button = QPushButton(ImportGroup)
        self.import_button.setObjectName("import_button")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.import_button.sizePolicy().hasHeightForWidth())
        self.import_button.setSizePolicy(sizePolicy)

        self.button_info_layout.addWidget(self.import_button)


        self.import_layout.setLayout(6, QFormLayout.ItemRole.FieldRole, self.button_info_layout)

        self.platform_label = QLabel(ImportGroup)
        self.platform_label.setObjectName("platform_label")

        self.import_layout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.platform_label)

        self.platform_layout = QHBoxLayout()
        self.platform_layout.setObjectName("platform_layout")
        self.platform_combo = QComboBox(ImportGroup)
        self.platform_combo.setObjectName("platform_combo")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.platform_combo.sizePolicy().hasHeightForWidth())
        self.platform_combo.setSizePolicy(sizePolicy1)

        self.platform_layout.addWidget(self.platform_combo)

        self.platform_info = QLabel(ImportGroup)
        self.platform_info.setObjectName("platform_info")
        self.platform_info.setFont(font)

        self.platform_layout.addWidget(self.platform_info)


        self.import_layout.setLayout(2, QFormLayout.ItemRole.FieldRole, self.platform_layout)


        self.retranslateUi(ImportGroup)
    # setupUi

    def retranslateUi(self, ImportGroup):
        ImportGroup.setTitle(QCoreApplication.translate("ImportGroup", "Import EGL game from a directory", None))
        self.path_edit_label.setText(QCoreApplication.translate("ImportGroup", "Installation path", None))
        self.app_name_label.setText(QCoreApplication.translate("ImportGroup", "Override app name", None))
        self.import_folder_label.setText(QCoreApplication.translate("ImportGroup", "Import all games", None))
        self.import_folder_check.setText(QCoreApplication.translate("ImportGroup", "Scan the installation path for game folders and import them", None))
        self.import_dlcs_label.setText(QCoreApplication.translate("ImportGroup", "Import DLCs", None))
        self.import_dlcs_check.setText(QCoreApplication.translate("ImportGroup", "If a game has DLCs, try to import them too", None))
        self.import_force_label.setText(QCoreApplication.translate("ImportGroup", "Force import", None))
        self.import_force_check.setText(QCoreApplication.translate("ImportGroup", "Import game despite missing files", None))
        self.import_button.setText(QCoreApplication.translate("ImportGroup", "Import game(s)", None))
        self.platform_label.setText(QCoreApplication.translate("ImportGroup", "Platform", None))
        self.platform_info.setText(QCoreApplication.translate("ImportGroup", "Select the native platform of the game", None))
    # retranslateUi


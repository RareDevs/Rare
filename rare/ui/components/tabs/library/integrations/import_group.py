# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'import_group.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QWidget)

class Ui_ImportGroup(object):
    def setupUi(self, ImportGroup):
        if not ImportGroup.objectName():
            ImportGroup.setObjectName(u"ImportGroup")
        ImportGroup.resize(651, 232)
        ImportGroup.setWindowTitle(u"ImportGroup")
        ImportGroup.setWindowFilePath(u"")
        self.import_layout = QFormLayout(ImportGroup)
        self.import_layout.setObjectName(u"import_layout")
        self.import_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.path_edit_label = QLabel(ImportGroup)
        self.path_edit_label.setObjectName(u"path_edit_label")

        self.import_layout.setWidget(0, QFormLayout.LabelRole, self.path_edit_label)

        self.app_name_label = QLabel(ImportGroup)
        self.app_name_label.setObjectName(u"app_name_label")

        self.import_layout.setWidget(1, QFormLayout.LabelRole, self.app_name_label)

        self.import_folder_label = QLabel(ImportGroup)
        self.import_folder_label.setObjectName(u"import_folder_label")

        self.import_layout.setWidget(3, QFormLayout.LabelRole, self.import_folder_label)

        self.import_folder_check = QCheckBox(ImportGroup)
        self.import_folder_check.setObjectName(u"import_folder_check")
        font = QFont()
        font.setItalic(True)
        self.import_folder_check.setFont(font)

        self.import_layout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.import_folder_check)

        self.import_dlcs_label = QLabel(ImportGroup)
        self.import_dlcs_label.setObjectName(u"import_dlcs_label")

        self.import_layout.setWidget(4, QFormLayout.LabelRole, self.import_dlcs_label)

        self.import_dlcs_check = QCheckBox(ImportGroup)
        self.import_dlcs_check.setObjectName(u"import_dlcs_check")
        self.import_dlcs_check.setFont(font)

        self.import_layout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.import_dlcs_check)

        self.import_force_label = QLabel(ImportGroup)
        self.import_force_label.setObjectName(u"import_force_label")

        self.import_layout.setWidget(5, QFormLayout.LabelRole, self.import_force_label)

        self.import_force_check = QCheckBox(ImportGroup)
        self.import_force_check.setObjectName(u"import_force_check")
        self.import_force_check.setFont(font)

        self.import_layout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.import_force_check)

        self.import_button_label = QLabel(ImportGroup)
        self.import_button_label.setObjectName(u"import_button_label")
        self.import_button_label.setText(u"error")

        self.import_layout.setWidget(6, QFormLayout.LabelRole, self.import_button_label)

        self.button_info_layout = QHBoxLayout()
        self.button_info_layout.setObjectName(u"button_info_layout")
        self.import_button = QPushButton(ImportGroup)
        self.import_button.setObjectName(u"import_button")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.import_button.sizePolicy().hasHeightForWidth())
        self.import_button.setSizePolicy(sizePolicy)

        self.button_info_layout.addWidget(self.import_button)


        self.import_layout.setLayout(6, QFormLayout.ItemRole.FieldRole, self.button_info_layout)

        self.platform_label = QLabel(ImportGroup)
        self.platform_label.setObjectName(u"platform_label")

        self.import_layout.setWidget(2, QFormLayout.LabelRole, self.platform_label)

        self.platform_layout = QHBoxLayout()
        self.platform_layout.setObjectName(u"platform_layout")
        self.platform_combo = QComboBox(ImportGroup)
        self.platform_combo.setObjectName(u"platform_combo")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.platform_combo.sizePolicy().hasHeightForWidth())
        self.platform_combo.setSizePolicy(sizePolicy1)

        self.platform_layout.addWidget(self.platform_combo)

        self.platform_tooltip = QLabel(ImportGroup)
        self.platform_tooltip.setObjectName(u"platform_tooltip")
        self.platform_tooltip.setFont(font)

        self.platform_layout.addWidget(self.platform_tooltip)


        self.import_layout.setLayout(2, QFormLayout.ItemRole.FieldRole, self.platform_layout)


        self.retranslateUi(ImportGroup)
    # setupUi

    def retranslateUi(self, ImportGroup):
        ImportGroup.setTitle(QCoreApplication.translate("ImportGroup", u"Import EGL game from a directory", None))
        self.path_edit_label.setText(QCoreApplication.translate("ImportGroup", u"Installation path", None))
        self.app_name_label.setText(QCoreApplication.translate("ImportGroup", u"Override app name", None))
        self.import_folder_label.setText(QCoreApplication.translate("ImportGroup", u"Import all games", None))
        self.import_folder_check.setText(QCoreApplication.translate("ImportGroup", u"Scan the installation path for game folders and import them", None))
        self.import_dlcs_label.setText(QCoreApplication.translate("ImportGroup", u"Import DLCs", None))
        self.import_dlcs_check.setText(QCoreApplication.translate("ImportGroup", u"If a game has DLCs, try to import them too", None))
        self.import_force_label.setText(QCoreApplication.translate("ImportGroup", u"Force import", None))
        self.import_force_check.setText(QCoreApplication.translate("ImportGroup", u"Import game despite missing files", None))
        self.import_button.setText(QCoreApplication.translate("ImportGroup", u"Import game(s)", None))
        self.platform_label.setText(QCoreApplication.translate("ImportGroup", u"Platform", None))
        self.platform_tooltip.setText(QCoreApplication.translate("ImportGroup", u"Select the native platform of the game", None))
    # retranslateUi


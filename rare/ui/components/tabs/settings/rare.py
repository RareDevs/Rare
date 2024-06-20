# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'rare.ui'
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
    QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_RareSettings(object):
    def setupUi(self, RareSettings):
        if not RareSettings.objectName():
            RareSettings.setObjectName(u"RareSettings")
        RareSettings.resize(629, 447)
        RareSettings.setWindowTitle(u"RareSettings")
        self.main_layout = QHBoxLayout(RareSettings)
        self.main_layout.setObjectName(u"main_layout")
        self.left_layout = QVBoxLayout()
        self.left_layout.setObjectName(u"left_layout")
        self.interface_group = QGroupBox(RareSettings)
        self.interface_group.setObjectName(u"interface_group")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.interface_group.sizePolicy().hasHeightForWidth())
        self.interface_group.setSizePolicy(sizePolicy)
        self.interface_layout = QFormLayout(self.interface_group)
        self.interface_layout.setObjectName(u"interface_layout")
        self.interface_layout.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        self.interface_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.lang_label = QLabel(self.interface_group)
        self.lang_label.setObjectName(u"lang_label")

        self.interface_layout.setWidget(0, QFormLayout.LabelRole, self.lang_label)

        self.lang_select = QComboBox(self.interface_group)
        self.lang_select.setObjectName(u"lang_select")

        self.interface_layout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.lang_select)

        self.color_label = QLabel(self.interface_group)
        self.color_label.setObjectName(u"color_label")

        self.interface_layout.setWidget(1, QFormLayout.LabelRole, self.color_label)

        self.color_select = QComboBox(self.interface_group)
        self.color_select.setObjectName(u"color_select")

        self.interface_layout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.color_select)

        self.style_label = QLabel(self.interface_group)
        self.style_label.setObjectName(u"style_label")

        self.interface_layout.setWidget(2, QFormLayout.LabelRole, self.style_label)

        self.style_select = QComboBox(self.interface_group)
        self.style_select.setObjectName(u"style_select")

        self.interface_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.style_select)

        self.interface_info = QLabel(self.interface_group)
        self.interface_info.setObjectName(u"interface_info")
        font = QFont()
        font.setItalic(True)
        self.interface_info.setFont(font)
        self.interface_info.setWordWrap(True)

        self.interface_layout.setWidget(4, QFormLayout.SpanningRole, self.interface_info)

        self.view_label = QLabel(self.interface_group)
        self.view_label.setObjectName(u"view_label")

        self.interface_layout.setWidget(3, QFormLayout.LabelRole, self.view_label)

        self.view_combo = QComboBox(self.interface_group)
        self.view_combo.setObjectName(u"view_combo")

        self.interface_layout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.view_combo)


        self.left_layout.addWidget(self.interface_group)

        self.settings_group = QGroupBox(RareSettings)
        self.settings_group.setObjectName(u"settings_group")
        self.behavior_layout = QGridLayout(self.settings_group)
        self.behavior_layout.setObjectName(u"behavior_layout")
        self.save_size = QCheckBox(self.settings_group)
        self.save_size.setObjectName(u"save_size")

        self.behavior_layout.addWidget(self.save_size, 5, 0, 1, 1)

        self.notification = QCheckBox(self.settings_group)
        self.notification.setObjectName(u"notification")

        self.behavior_layout.addWidget(self.notification, 4, 0, 1, 1)

        self.log_games = QCheckBox(self.settings_group)
        self.log_games.setObjectName(u"log_games")

        self.behavior_layout.addWidget(self.log_games, 6, 0, 1, 1)

        self.sys_tray = QCheckBox(self.settings_group)
        self.sys_tray.setObjectName(u"sys_tray")

        self.behavior_layout.addWidget(self.sys_tray, 0, 0, 1, 1)

        self.auto_update = QCheckBox(self.settings_group)
        self.auto_update.setObjectName(u"auto_update")

        self.behavior_layout.addWidget(self.auto_update, 1, 0, 1, 1)

        self.confirm_start = QCheckBox(self.settings_group)
        self.confirm_start.setObjectName(u"confirm_start")

        self.behavior_layout.addWidget(self.confirm_start, 2, 0, 1, 1)

        self.auto_sync_cloud = QCheckBox(self.settings_group)
        self.auto_sync_cloud.setObjectName(u"auto_sync_cloud")

        self.behavior_layout.addWidget(self.auto_sync_cloud, 3, 0, 1, 1)

        self.settings_hspacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.behavior_layout.addItem(self.settings_hspacer, 2, 1, 2, 1)


        self.left_layout.addWidget(self.settings_group)

        self.left_vspacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.left_layout.addItem(self.left_vspacer)


        self.main_layout.addLayout(self.left_layout)

        self.right_layout = QVBoxLayout()
        self.right_layout.setObjectName(u"right_layout")
        self.log_dir_group = QGroupBox(RareSettings)
        self.log_dir_group.setObjectName(u"log_dir_group")
        self.log_dir_layout = QVBoxLayout(self.log_dir_group)
        self.log_dir_layout.setObjectName(u"log_dir_layout")
        self.log_dir_open_button = QPushButton(self.log_dir_group)
        self.log_dir_open_button.setObjectName(u"log_dir_open_button")

        self.log_dir_layout.addWidget(self.log_dir_open_button)

        self.log_dir_clean_button = QPushButton(self.log_dir_group)
        self.log_dir_clean_button.setObjectName(u"log_dir_clean_button")

        self.log_dir_layout.addWidget(self.log_dir_clean_button)

        self.log_dir_size_label = QLabel(self.log_dir_group)
        self.log_dir_size_label.setObjectName(u"log_dir_size_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.log_dir_size_label.sizePolicy().hasHeightForWidth())
        self.log_dir_size_label.setSizePolicy(sizePolicy1)
        self.log_dir_size_label.setText(u"")
        self.log_dir_size_label.setWordWrap(True)

        self.log_dir_layout.addWidget(self.log_dir_size_label)


        self.right_layout.addWidget(self.log_dir_group)

        self.groupBox = QGroupBox(RareSettings)
        self.groupBox.setObjectName(u"groupBox")
        self.shortcuts_layout = QVBoxLayout(self.groupBox)
        self.shortcuts_layout.setObjectName(u"shortcuts_layout")
        self.desktop_link_btn = QPushButton(self.groupBox)
        self.desktop_link_btn.setObjectName(u"desktop_link_btn")

        self.shortcuts_layout.addWidget(self.desktop_link_btn)

        self.startmenu_link_btn = QPushButton(self.groupBox)
        self.startmenu_link_btn.setObjectName(u"startmenu_link_btn")

        self.shortcuts_layout.addWidget(self.startmenu_link_btn)


        self.right_layout.addWidget(self.groupBox)

        self.right_vspacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.right_layout.addItem(self.right_vspacer)


        self.main_layout.addLayout(self.right_layout)


        self.retranslateUi(RareSettings)
    # setupUi

    def retranslateUi(self, RareSettings):
        self.interface_group.setTitle(QCoreApplication.translate("RareSettings", u"Interface", None))
        self.lang_label.setText(QCoreApplication.translate("RareSettings", u"Language", None))
        self.color_label.setText(QCoreApplication.translate("RareSettings", u"Color scheme", None))
        self.style_label.setText(QCoreApplication.translate("RareSettings", u"Style sheet", None))
        self.interface_info.setText(QCoreApplication.translate("RareSettings", u"Restart Rare to apply changes.", None))
        self.view_label.setText(QCoreApplication.translate("RareSettings", u"Library view", None))
        self.settings_group.setTitle(QCoreApplication.translate("RareSettings", u"Behavior", None))
        self.save_size.setText(QCoreApplication.translate("RareSettings", u"Restore window size on application startup", None))
        self.notification.setText(QCoreApplication.translate("RareSettings", u"Show notifications when downloads complete", None))
        self.log_games.setText(QCoreApplication.translate("RareSettings", u"Show console window when launching games", None))
        self.sys_tray.setText(QCoreApplication.translate("RareSettings", u"Close to system tray", None))
        self.auto_update.setText(QCoreApplication.translate("RareSettings", u"Queue game updates on application startup", None))
        self.confirm_start.setText(QCoreApplication.translate("RareSettings", u"Confirm before launching games", None))
        self.auto_sync_cloud.setText(QCoreApplication.translate("RareSettings", u"Automatically upload/download cloud saves", None))
        self.log_dir_group.setTitle(QCoreApplication.translate("RareSettings", u"Logs", None))
        self.log_dir_open_button.setText(QCoreApplication.translate("RareSettings", u"Open log folder", None))
        self.log_dir_clean_button.setText(QCoreApplication.translate("RareSettings", u"Clean log folder", None))
        self.groupBox.setTitle(QCoreApplication.translate("RareSettings", u"Shortcuts", None))
        self.desktop_link_btn.setText(QCoreApplication.translate("RareSettings", u"Create on desktop", None))
        self.startmenu_link_btn.setText(QCoreApplication.translate("RareSettings", u"Create in menu", None))
        pass
    # retranslateUi


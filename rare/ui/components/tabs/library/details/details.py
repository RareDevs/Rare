# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'details.ui'
##
## Created by: Qt User Interface Compiler version 6.9.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


class Ui_GameDetails(object):
    def setupUi(self, GameDetails):
        if not GameDetails.objectName():
            GameDetails.setObjectName(u"GameDetails")
        GameDetails.resize(795, 404)
        GameDetails.setWindowTitle(u"GameDetails")
        self.main_layout = QHBoxLayout(GameDetails)
        self.main_layout.setObjectName(u"main_layout")
        self.left_layout = QVBoxLayout()
        self.left_layout.setObjectName(u"left_layout")
        self.tags_group = QGroupBox(GameDetails)
        self.tags_group.setObjectName(u"tags_group")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tags_group.sizePolicy().hasHeightForWidth())
        self.tags_group.setSizePolicy(sizePolicy)
        self.tags_group_layout = QVBoxLayout(self.tags_group)
        self.tags_group_layout.setObjectName(u"tags_group_layout")
        self.add_tag_button = QPushButton(self.tags_group)
        self.add_tag_button.setObjectName(u"add_tag_button")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.add_tag_button.sizePolicy().hasHeightForWidth())
        self.add_tag_button.setSizePolicy(sizePolicy1)

        self.tags_group_layout.addWidget(self.add_tag_button, 0, Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTop)

        self.tags_vlayout = QVBoxLayout()
        self.tags_vlayout.setObjectName(u"tags_vlayout")

        self.tags_group_layout.addLayout(self.tags_vlayout)


        self.left_layout.addWidget(self.tags_group)


        self.main_layout.addLayout(self.left_layout)

        self.right_layout = QGridLayout()
        self.right_layout.setSpacing(24)
        self.right_layout.setObjectName(u"right_layout")
        self.details_layout = QFormLayout()
        self.details_layout.setObjectName(u"details_layout")
        self.details_layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.details_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.details_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.details_layout.setHorizontalSpacing(12)
        self.details_layout.setVerticalSpacing(12)
        self.details_layout.setContentsMargins(12, -1, -1, -1)
        self.dev_label = QLabel(GameDetails)
        self.dev_label.setObjectName(u"dev_label")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.dev_label.sizePolicy().hasHeightForWidth())
        self.dev_label.setSizePolicy(sizePolicy2)
        font = QFont()
        font.setBold(True)
        self.dev_label.setFont(font)
        self.dev_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.details_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.dev_label)

        self.dev = QLabel(GameDetails)
        self.dev.setObjectName(u"dev")
        self.dev.setText(u"error")
        self.dev.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.details_layout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.dev)

        self.app_name_label = QLabel(GameDetails)
        self.app_name_label.setObjectName(u"app_name_label")
        sizePolicy2.setHeightForWidth(self.app_name_label.sizePolicy().hasHeightForWidth())
        self.app_name_label.setSizePolicy(sizePolicy2)
        self.app_name_label.setFont(font)
        self.app_name_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.details_layout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.app_name_label)

        self.app_name = QLabel(GameDetails)
        self.app_name.setObjectName(u"app_name")
        self.app_name.setText(u"error")
        self.app_name.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.details_layout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.app_name)

        self.version_label = QLabel(GameDetails)
        self.version_label.setObjectName(u"version_label")
        sizePolicy2.setHeightForWidth(self.version_label.sizePolicy().hasHeightForWidth())
        self.version_label.setSizePolicy(sizePolicy2)
        self.version_label.setFont(font)
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.details_layout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.version_label)

        self.version = QLabel(GameDetails)
        self.version.setObjectName(u"version")
        self.version.setText(u"error")
        self.version.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.details_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.version)

        self.grade_label = QLabel(GameDetails)
        self.grade_label.setObjectName(u"grade_label")
        sizePolicy2.setHeightForWidth(self.grade_label.sizePolicy().hasHeightForWidth())
        self.grade_label.setSizePolicy(sizePolicy2)
        self.grade_label.setFont(font)
        self.grade_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.details_layout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.grade_label)

        self.grade = QLabel(GameDetails)
        self.grade.setObjectName(u"grade")
        self.grade.setText(u"error")
        self.grade.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.details_layout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.grade)

        self.install_size_label = QLabel(GameDetails)
        self.install_size_label.setObjectName(u"install_size_label")
        sizePolicy2.setHeightForWidth(self.install_size_label.sizePolicy().hasHeightForWidth())
        self.install_size_label.setSizePolicy(sizePolicy2)
        self.install_size_label.setFont(font)
        self.install_size_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.details_layout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.install_size_label)

        self.install_size = QLabel(GameDetails)
        self.install_size.setObjectName(u"install_size")
        self.install_size.setText(u"error")
        self.install_size.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.details_layout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.install_size)

        self.install_path_label = QLabel(GameDetails)
        self.install_path_label.setObjectName(u"install_path_label")
        sizePolicy2.setHeightForWidth(self.install_path_label.sizePolicy().hasHeightForWidth())
        self.install_path_label.setSizePolicy(sizePolicy2)
        self.install_path_label.setFont(font)
        self.install_path_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.details_layout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.install_path_label)

        self.install_path = QLabel(GameDetails)
        self.install_path.setObjectName(u"install_path")
        self.install_path.setText(u"error")
        self.install_path.setWordWrap(True)
        self.install_path.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.details_layout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.install_path)

        self.platform_label = QLabel(GameDetails)
        self.platform_label.setObjectName(u"platform_label")
        sizePolicy2.setHeightForWidth(self.platform_label.sizePolicy().hasHeightForWidth())
        self.platform_label.setSizePolicy(sizePolicy2)
        self.platform_label.setFont(font)
        self.platform_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.details_layout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.platform_label)

        self.platform = QLabel(GameDetails)
        self.platform.setObjectName(u"platform")
        self.platform.setText(u"error")

        self.details_layout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.platform)

        self.actions_label = QLabel(GameDetails)
        self.actions_label.setObjectName(u"actions_label")
        sizePolicy2.setHeightForWidth(self.actions_label.sizePolicy().hasHeightForWidth())
        self.actions_label.setSizePolicy(sizePolicy2)
        self.actions_label.setFont(font)
        self.actions_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.details_layout.setWidget(7, QFormLayout.ItemRole.LabelRole, self.actions_label)

        self.actions_stack = QStackedWidget(GameDetails)
        self.actions_stack.setObjectName(u"actions_stack")
        sizePolicy.setHeightForWidth(self.actions_stack.sizePolicy().hasHeightForWidth())
        self.actions_stack.setSizePolicy(sizePolicy)
        self.actions_stack.setMinimumSize(QSize(300, 0))
        self.actions_stack.setMaximumSize(QSize(300, 16777215))
        self.installed_page = QWidget()
        self.installed_page.setObjectName(u"installed_page")
        self.installed_layout = QVBoxLayout(self.installed_page)
        self.installed_layout.setObjectName(u"installed_layout")
        self.installed_layout.setContentsMargins(0, 0, 0, 0)
        self.modify_button = QPushButton(self.installed_page)
        self.modify_button.setObjectName(u"modify_button")

        self.installed_layout.addWidget(self.modify_button)

        self.verify_stack = QStackedWidget(self.installed_page)
        self.verify_stack.setObjectName(u"verify_stack")
        self.verify_button_page = QWidget()
        self.verify_button_page.setObjectName(u"verify_button_page")
        self.verify_page_layout = QHBoxLayout(self.verify_button_page)
        self.verify_page_layout.setSpacing(0)
        self.verify_page_layout.setObjectName(u"verify_page_layout")
        self.verify_page_layout.setContentsMargins(0, 0, 0, 0)
        self.verify_button = QPushButton(self.verify_button_page)
        self.verify_button.setObjectName(u"verify_button")

        self.verify_page_layout.addWidget(self.verify_button)

        self.verify_stack.addWidget(self.verify_button_page)
        self.verify_progress_page = QWidget()
        self.verify_progress_page.setObjectName(u"verify_progress_page")
        self.verify_progress_layout = QHBoxLayout(self.verify_progress_page)
        self.verify_progress_layout.setSpacing(0)
        self.verify_progress_layout.setObjectName(u"verify_progress_layout")
        self.verify_progress_layout.setContentsMargins(0, 0, 0, 0)
        self.verify_progress = QProgressBar(self.verify_progress_page)
        self.verify_progress.setObjectName(u"verify_progress")
        self.verify_progress.setValue(24)

        self.verify_progress_layout.addWidget(self.verify_progress)

        self.verify_stack.addWidget(self.verify_progress_page)

        self.installed_layout.addWidget(self.verify_stack)

        self.repair_button = QPushButton(self.installed_page)
        self.repair_button.setObjectName(u"repair_button")

        self.installed_layout.addWidget(self.repair_button)

        self.move_stack = QStackedWidget(self.installed_page)
        self.move_stack.setObjectName(u"move_stack")
        self.move_button_page = QWidget()
        self.move_button_page.setObjectName(u"move_button_page")
        self.move_button_layout = QHBoxLayout(self.move_button_page)
        self.move_button_layout.setSpacing(0)
        self.move_button_layout.setObjectName(u"move_button_layout")
        self.move_button_layout.setContentsMargins(0, 0, 0, 0)
        self.move_button = QPushButton(self.move_button_page)
        self.move_button.setObjectName(u"move_button")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.move_button.sizePolicy().hasHeightForWidth())
        self.move_button.setSizePolicy(sizePolicy3)

        self.move_button_layout.addWidget(self.move_button)

        self.move_stack.addWidget(self.move_button_page)
        self.move_progress_page = QWidget()
        self.move_progress_page.setObjectName(u"move_progress_page")
        self.move_progress_layout = QHBoxLayout(self.move_progress_page)
        self.move_progress_layout.setSpacing(0)
        self.move_progress_layout.setObjectName(u"move_progress_layout")
        self.move_progress_layout.setContentsMargins(0, 0, 0, 0)
        self.move_progress = QProgressBar(self.move_progress_page)
        self.move_progress.setObjectName(u"move_progress")
        self.move_progress.setValue(24)

        self.move_progress_layout.addWidget(self.move_progress)

        self.move_stack.addWidget(self.move_progress_page)

        self.installed_layout.addWidget(self.move_stack)

        self.uninstall_button = QPushButton(self.installed_page)
        self.uninstall_button.setObjectName(u"uninstall_button")

        self.installed_layout.addWidget(self.uninstall_button)

        self.actions_stack.addWidget(self.installed_page)
        self.uninstalled_page = QWidget()
        self.uninstalled_page.setObjectName(u"uninstalled_page")
        self.uninstalled_layout = QVBoxLayout(self.uninstalled_page)
        self.uninstalled_layout.setObjectName(u"uninstalled_layout")
        self.uninstalled_layout.setContentsMargins(0, 0, 0, 0)
        self.install_button = QPushButton(self.uninstalled_page)
        self.install_button.setObjectName(u"install_button")

        self.uninstalled_layout.addWidget(self.install_button)

        self.import_button = QPushButton(self.uninstalled_page)
        self.import_button.setObjectName(u"import_button")

        self.uninstalled_layout.addWidget(self.import_button)

        self.uninstalled_page_bot_vspacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.uninstalled_layout.addItem(self.uninstalled_page_bot_vspacer)

        self.actions_stack.addWidget(self.uninstalled_page)

        self.details_layout.setWidget(7, QFormLayout.ItemRole.FieldRole, self.actions_stack)


        self.right_layout.addLayout(self.details_layout, 0, 0, 1, 1)

        self.description_label = QTextBrowser(GameDetails)
        self.description_label.setObjectName(u"description_label")
        self.description_label.setOpenExternalLinks(True)

        self.right_layout.addWidget(self.description_label, 0, 1, 1, 1)

        self.requirements_group = QFrame(GameDetails)
        self.requirements_group.setObjectName(u"requirements_group")
        self.requirements_group.setFrameShape(QFrame.Shape.StyledPanel)
        self.requirements_group.setFrameShadow(QFrame.Shadow.Sunken)
        self.requirements_layout = QHBoxLayout(self.requirements_group)
        self.requirements_layout.setObjectName(u"requirements_layout")
        self.requirements_layout.setContentsMargins(0, 0, 0, 0)

        self.right_layout.addWidget(self.requirements_group, 1, 0, 1, 2, Qt.AlignmentFlag.AlignBottom)

        self.right_layout.setRowStretch(1, 1)
        self.right_layout.setColumnStretch(1, 1)

        self.main_layout.addLayout(self.right_layout)

        self.main_layout.setStretch(1, 1)

        self.retranslateUi(GameDetails)

        self.actions_stack.setCurrentIndex(0)
        self.verify_stack.setCurrentIndex(0)
        self.move_stack.setCurrentIndex(0)

    # setupUi

    def retranslateUi(self, GameDetails):
        self.tags_group.setTitle(QCoreApplication.translate("GameDetails", u"Tags", None))
#if QT_CONFIG(tooltip)
        self.add_tag_button.setToolTip(QCoreApplication.translate("GameDetails", u"Add custom tag", None))
#endif // QT_CONFIG(tooltip)
        self.add_tag_button.setText(QCoreApplication.translate("GameDetails", u"Add tag", None))
        self.dev_label.setText(QCoreApplication.translate("GameDetails", u"Developer", None))
        self.app_name_label.setText(QCoreApplication.translate("GameDetails", u"Application name", None))
        self.version_label.setText(QCoreApplication.translate("GameDetails", u"Version", None))
        self.grade_label.setText(QCoreApplication.translate("GameDetails", u"ProtonDB grade", None))
        self.install_size_label.setText(QCoreApplication.translate("GameDetails", u"Installation size", None))
        self.install_path_label.setText(QCoreApplication.translate("GameDetails", u"Installation path", None))
        self.platform_label.setText(QCoreApplication.translate("GameDetails", u"Platform", None))
        self.actions_label.setText(QCoreApplication.translate("GameDetails", u"Actions", None))
        self.modify_button.setText(QCoreApplication.translate("GameDetails", u"Modify", None))
        self.verify_button.setText(QCoreApplication.translate("GameDetails", u"Verify", None))
        self.repair_button.setText(QCoreApplication.translate("GameDetails", u"Repair", None))
        self.move_button.setText(QCoreApplication.translate("GameDetails", u"Move", None))
        self.uninstall_button.setText(QCoreApplication.translate("GameDetails", u"Uninstall", None))
        self.install_button.setText(QCoreApplication.translate("GameDetails", u"Install", None))
        self.import_button.setText(QCoreApplication.translate("GameDetails", u"Import", None))
        pass
    # retranslateUi


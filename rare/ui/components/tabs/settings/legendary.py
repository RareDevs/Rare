
################################################################################
## Form generated from reading UI file 'legendary.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QVBoxLayout,
)


class Ui_LegendarySettings:
    def setupUi(self, LegendarySettings):
        if not LegendarySettings.objectName():
            LegendarySettings.setObjectName("LegendarySettings")
        LegendarySettings.resize(641, 420)
        LegendarySettings.setWindowTitle("LegendarySettings")
        self.legendary_layout = QHBoxLayout(LegendarySettings)
        self.legendary_layout.setObjectName("legendary_layout")
        self.left_layout = QVBoxLayout()
        self.left_layout.setObjectName("left_layout")
        self.install_dir_group = QGroupBox(LegendarySettings)
        self.install_dir_group.setObjectName("install_dir_group")
        self.install_dir_group.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.install_dir_layout = QVBoxLayout(self.install_dir_group)
        self.install_dir_layout.setObjectName("install_dir_layout")

        self.left_layout.addWidget(self.install_dir_group)

        self.download_group = QGroupBox(LegendarySettings)
        self.download_group.setObjectName("download_group")
        self.download_group.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.download_layout = QFormLayout(self.download_group)
        self.download_layout.setObjectName("download_layout")
        self.download_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.max_workers_label = QLabel(self.download_group)
        self.max_workers_label.setObjectName("max_workers_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.max_workers_label.sizePolicy().hasHeightForWidth())
        self.max_workers_label.setSizePolicy(sizePolicy)

        self.download_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.max_workers_label)

        self.max_workers_layout = QHBoxLayout()
        self.max_workers_layout.setObjectName("max_workers_layout")
        self.max_worker_spin = QSpinBox(self.download_group)
        self.max_worker_spin.setObjectName("max_worker_spin")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.max_worker_spin.sizePolicy().hasHeightForWidth())
        self.max_worker_spin.setSizePolicy(sizePolicy1)
        self.max_worker_spin.setMinimum(0)
        self.max_worker_spin.setMaximum(16)
        self.max_worker_spin.setValue(0)

        self.max_workers_layout.addWidget(self.max_worker_spin)

        self.max_workers_info_label = QLabel(self.download_group)
        self.max_workers_info_label.setObjectName("max_workers_info_label")
        font = QFont()
        font.setItalic(True)
        self.max_workers_info_label.setFont(font)

        self.max_workers_layout.addWidget(self.max_workers_info_label)


        self.download_layout.setLayout(0, QFormLayout.ItemRole.FieldRole, self.max_workers_layout)

        self.max_memory_label = QLabel(self.download_group)
        self.max_memory_label.setObjectName("max_memory_label")

        self.download_layout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.max_memory_label)

        self.max_memory_layout = QHBoxLayout()
        self.max_memory_layout.setObjectName("max_memory_layout")
        self.max_memory_spin = QSpinBox(self.download_group)
        self.max_memory_spin.setObjectName("max_memory_spin")
        sizePolicy1.setHeightForWidth(self.max_memory_spin.sizePolicy().hasHeightForWidth())
        self.max_memory_spin.setSizePolicy(sizePolicy1)
        self.max_memory_spin.setMinimum(0)
        self.max_memory_spin.setMaximum(10240)
        self.max_memory_spin.setSingleStep(128)
        self.max_memory_spin.setValue(1024)

        self.max_memory_layout.addWidget(self.max_memory_spin)

        self.max_memory_info_label = QLabel(self.download_group)
        self.max_memory_info_label.setObjectName("max_memory_info_label")
        self.max_memory_info_label.setFont(font)

        self.max_memory_layout.addWidget(self.max_memory_info_label)


        self.download_layout.setLayout(1, QFormLayout.ItemRole.FieldRole, self.max_memory_layout)

        self.preferred_cdn_label = QLabel(self.download_group)
        self.preferred_cdn_label.setObjectName("preferred_cdn_label")

        self.download_layout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.preferred_cdn_label)

        self.preferred_cdn_line = QLineEdit(self.download_group)
        self.preferred_cdn_line.setObjectName("preferred_cdn_line")

        self.download_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.preferred_cdn_line)

        self.disable_https_label = QLabel(self.download_group)
        self.disable_https_label.setObjectName("disable_https_label")

        self.download_layout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.disable_https_label)

        self.disable_https_check = QCheckBox(self.download_group)
        self.disable_https_check.setObjectName("disable_https_check")

        self.download_layout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.disable_https_check)


        self.left_layout.addWidget(self.download_group)

        self.left_vspacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.left_layout.addItem(self.left_vspacer)


        self.legendary_layout.addLayout(self.left_layout)

        self.right_layout = QVBoxLayout()
        self.right_layout.setObjectName("right_layout")
        self.locale_group = QGroupBox(LegendarySettings)
        self.locale_group.setObjectName("locale_group")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.locale_group.sizePolicy().hasHeightForWidth())
        self.locale_group.setSizePolicy(sizePolicy2)
        self.locale_group.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.locale_layout = QVBoxLayout(self.locale_group)
        self.locale_layout.setObjectName("locale_layout")

        self.right_layout.addWidget(self.locale_group)

        self.cleanup_group = QGroupBox(LegendarySettings)
        self.cleanup_group.setObjectName("cleanup_group")
        self.cleanup_group.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.cleanup_layout = QVBoxLayout(self.cleanup_group)
        self.cleanup_layout.setObjectName("cleanup_layout")
        self.clean_keep_manifests_button = QPushButton(self.cleanup_group)
        self.clean_keep_manifests_button.setObjectName("clean_keep_manifests_button")

        self.cleanup_layout.addWidget(self.clean_keep_manifests_button)

        self.clean_button = QPushButton(self.cleanup_group)
        self.clean_button.setObjectName("clean_button")

        self.cleanup_layout.addWidget(self.clean_button)


        self.right_layout.addWidget(self.cleanup_group)

        self.metadata_group = QGroupBox(LegendarySettings)
        self.metadata_group.setObjectName("metadata_group")
        self.metadata_layout = QVBoxLayout(self.metadata_group)
        self.metadata_layout.setObjectName("metadata_layout")
        self.fetch_win32_check = QCheckBox(self.metadata_group)
        self.fetch_win32_check.setObjectName("fetch_win32_check")

        self.metadata_layout.addWidget(self.fetch_win32_check)

        self.fetch_macos_check = QCheckBox(self.metadata_group)
        self.fetch_macos_check.setObjectName("fetch_macos_check")

        self.metadata_layout.addWidget(self.fetch_macos_check)

        self.fetch_unreal_check = QCheckBox(self.metadata_group)
        self.fetch_unreal_check.setObjectName("fetch_unreal_check")

        self.metadata_layout.addWidget(self.fetch_unreal_check)

        self.exclude_non_asset_check = QCheckBox(self.metadata_group)
        self.exclude_non_asset_check.setObjectName("exclude_non_asset_check")

        self.metadata_layout.addWidget(self.exclude_non_asset_check)

        self.metadata_info = QLabel(self.metadata_group)
        self.metadata_info.setObjectName("metadata_info")
        self.metadata_info.setFont(font)

        self.metadata_layout.addWidget(self.metadata_info)

        self.refresh_metadata_button = QPushButton(self.metadata_group)
        self.refresh_metadata_button.setObjectName("refresh_metadata_button")

        self.metadata_layout.addWidget(self.refresh_metadata_button)


        self.right_layout.addWidget(self.metadata_group)

        self.right_vspacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.right_layout.addItem(self.right_vspacer)


        self.legendary_layout.addLayout(self.right_layout)


        self.retranslateUi(LegendarySettings)
    # setupUi

    def retranslateUi(self, LegendarySettings):
        self.install_dir_group.setTitle(QCoreApplication.translate("LegendarySettings", "Installation folder", None))
        self.download_group.setTitle(QCoreApplication.translate("LegendarySettings", "Download settings", None))
        self.max_workers_label.setText(QCoreApplication.translate("LegendarySettings", "Max workers", None))
        self.max_workers_info_label.setText(QCoreApplication.translate("LegendarySettings", "Less is slower (0: Default)", None))
        self.max_memory_label.setText(QCoreApplication.translate("LegendarySettings", "Max shared memory", None))
        self.max_memory_spin.setSuffix(QCoreApplication.translate("LegendarySettings", "MiB", None))
        self.max_memory_info_label.setText(QCoreApplication.translate("LegendarySettings", "Less is slower (0: Default)", None))
        self.preferred_cdn_label.setText(QCoreApplication.translate("LegendarySettings", "Preferred CDN", None))
        self.preferred_cdn_line.setPlaceholderText(QCoreApplication.translate("LegendarySettings", "Default", None))
        self.disable_https_label.setText(QCoreApplication.translate("LegendarySettings", "Disable HTTPS", None))
        self.disable_https_check.setText("")
        self.locale_group.setTitle(QCoreApplication.translate("LegendarySettings", "Locale", None))
        self.cleanup_group.setTitle(QCoreApplication.translate("LegendarySettings", "Cleanup", None))
        self.clean_keep_manifests_button.setText(QCoreApplication.translate("LegendarySettings", "Clean, but keep manifests", None))
        self.clean_button.setText(QCoreApplication.translate("LegendarySettings", "Remove everything", None))
        self.metadata_group.setTitle(QCoreApplication.translate("LegendarySettings", "Platforms", None))
        self.fetch_win32_check.setText(QCoreApplication.translate("LegendarySettings", "Include Win32 games", None))
        self.fetch_macos_check.setText(QCoreApplication.translate("LegendarySettings", "Include macOS games", None))
        self.fetch_unreal_check.setText(QCoreApplication.translate("LegendarySettings", "Include Unreal engine", None))
#if QT_CONFIG(tooltip)
        self.exclude_non_asset_check.setToolTip(QCoreApplication.translate("LegendarySettings", "Do not load metadata for non-asset games (i.e. Origin games) on start-up.\n"
"\n"
"Disabling this greatly improves start-up time, but some games might not be visible in your library.", None))
#endif // QT_CONFIG(tooltip)
        self.exclude_non_asset_check.setText(QCoreApplication.translate("LegendarySettings", "Exclude non-asset games", None))
        self.metadata_info.setText(QCoreApplication.translate("LegendarySettings", "Restart Rare to apply", None))
        self.refresh_metadata_button.setText(QCoreApplication.translate("LegendarySettings", "Refresh metadata", None))
        pass
    # retranslateUi



################################################################################
## Form generated from reading UI file 'advanced.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QCheckBox, QFormLayout, QHBoxLayout, QLabel, QSizePolicy, QSpinBox


class Ui_InstallDialogAdvanced:
    def setupUi(self, InstallDialogAdvanced):
        if not InstallDialogAdvanced.objectName():
            InstallDialogAdvanced.setObjectName("InstallDialogAdvanced")
        InstallDialogAdvanced.resize(393, 209)
        InstallDialogAdvanced.setWindowTitle("InstallDialogAdvanced")
        self.main_layout = QFormLayout(InstallDialogAdvanced)
        self.main_layout.setObjectName("main_layout")
        self.main_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.max_workers_label = QLabel(InstallDialogAdvanced)
        self.max_workers_label.setObjectName("max_workers_label")
        self.max_workers_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.main_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.max_workers_label)

        self.max_workers_layout = QHBoxLayout()
        self.max_workers_layout.setObjectName("max_workers_layout")
        self.max_workers_spin = QSpinBox(InstallDialogAdvanced)
        self.max_workers_spin.setObjectName("max_workers_spin")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.max_workers_spin.sizePolicy().hasHeightForWidth())
        self.max_workers_spin.setSizePolicy(sizePolicy)

        self.max_workers_layout.addWidget(self.max_workers_spin)

        self.max_workers_info = QLabel(InstallDialogAdvanced)
        self.max_workers_info.setObjectName("max_workers_info")
        font = QFont()
        font.setItalic(True)
        self.max_workers_info.setFont(font)

        self.max_workers_layout.addWidget(self.max_workers_info)


        self.main_layout.setLayout(0, QFormLayout.ItemRole.FieldRole, self.max_workers_layout)

        self.max_memory_label = QLabel(InstallDialogAdvanced)
        self.max_memory_label.setObjectName("max_memory_label")
        self.max_memory_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.main_layout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.max_memory_label)

        self.max_memory_layout = QHBoxLayout()
        self.max_memory_layout.setObjectName("max_memory_layout")
        self.max_memory_spin = QSpinBox(InstallDialogAdvanced)
        self.max_memory_spin.setObjectName("max_memory_spin")
        sizePolicy.setHeightForWidth(self.max_memory_spin.sizePolicy().hasHeightForWidth())
        self.max_memory_spin.setSizePolicy(sizePolicy)
        self.max_memory_spin.setMinimum(0)
        self.max_memory_spin.setMaximum(10240)
        self.max_memory_spin.setSingleStep(128)
        self.max_memory_spin.setValue(1024)

        self.max_memory_layout.addWidget(self.max_memory_spin)

        self.max_memory_info = QLabel(InstallDialogAdvanced)
        self.max_memory_info.setObjectName("max_memory_info")
        self.max_memory_info.setFont(font)

        self.max_memory_layout.addWidget(self.max_memory_info)


        self.main_layout.setLayout(1, QFormLayout.ItemRole.FieldRole, self.max_memory_layout)

        self.install_prereqs_label = QLabel(InstallDialogAdvanced)
        self.install_prereqs_label.setObjectName("install_prereqs_label")

        self.main_layout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.install_prereqs_label)

        self.install_prereqs_check = QCheckBox(InstallDialogAdvanced)
        self.install_prereqs_check.setObjectName("install_prereqs_check")
        self.install_prereqs_check.setFont(font)
        self.install_prereqs_check.setChecked(False)

        self.main_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.install_prereqs_check)

        self.read_files_label = QLabel(InstallDialogAdvanced)
        self.read_files_label.setObjectName("read_files_label")

        self.main_layout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.read_files_label)

        self.read_files_check = QCheckBox(InstallDialogAdvanced)
        self.read_files_check.setObjectName("read_files_check")
        self.read_files_check.setFont(font)

        self.main_layout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.read_files_check)

        self.dl_optimizations_label = QLabel(InstallDialogAdvanced)
        self.dl_optimizations_label.setObjectName("dl_optimizations_label")

        self.main_layout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.dl_optimizations_label)

        self.dl_optimizations_check = QCheckBox(InstallDialogAdvanced)
        self.dl_optimizations_check.setObjectName("dl_optimizations_check")
        self.dl_optimizations_check.setFont(font)
        self.dl_optimizations_check.setChecked(False)

        self.main_layout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.dl_optimizations_check)

        self.force_download_label = QLabel(InstallDialogAdvanced)
        self.force_download_label.setObjectName("force_download_label")

        self.main_layout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.force_download_label)

        self.force_download_check = QCheckBox(InstallDialogAdvanced)
        self.force_download_check.setObjectName("force_download_check")
        self.force_download_check.setFont(font)

        self.main_layout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.force_download_check)

        self.ignore_space_label = QLabel(InstallDialogAdvanced)
        self.ignore_space_label.setObjectName("ignore_space_label")

        self.main_layout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.ignore_space_label)

        self.ignore_space_check = QCheckBox(InstallDialogAdvanced)
        self.ignore_space_check.setObjectName("ignore_space_check")
        self.ignore_space_check.setFont(font)

        self.main_layout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.ignore_space_check)

        self.download_only_label = QLabel(InstallDialogAdvanced)
        self.download_only_label.setObjectName("download_only_label")

        self.main_layout.setWidget(7, QFormLayout.ItemRole.LabelRole, self.download_only_label)

        self.download_only_check = QCheckBox(InstallDialogAdvanced)
        self.download_only_check.setObjectName("download_only_check")
        self.download_only_check.setFont(font)

        self.main_layout.setWidget(7, QFormLayout.ItemRole.FieldRole, self.download_only_check)


        self.retranslateUi(InstallDialogAdvanced)
    # setupUi

    def retranslateUi(self, InstallDialogAdvanced):
        self.max_workers_label.setText(QCoreApplication.translate("InstallDialogAdvanced", "Max workers", None))
#if QT_CONFIG(tooltip)
        self.max_workers_spin.setToolTip(QCoreApplication.translate("InstallDialogAdvanced", "Maximum amount of download workers, default: min(2 * CPUs, 16).", None))
#endif // QT_CONFIG(tooltip)
        self.max_workers_info.setText(QCoreApplication.translate("InstallDialogAdvanced", "Less is slower. (0: Default)", None))
        self.max_memory_label.setText(QCoreApplication.translate("InstallDialogAdvanced", "Max shared memory", None))
#if QT_CONFIG(tooltip)
        self.max_memory_spin.setToolTip(QCoreApplication.translate("InstallDialogAdvanced", "Maximum amount of shared memory to use (in MiB), default: 1 GiB.", None))
#endif // QT_CONFIG(tooltip)
        self.max_memory_spin.setSuffix(QCoreApplication.translate("InstallDialogAdvanced", "MiB", None))
        self.max_memory_info.setText(QCoreApplication.translate("InstallDialogAdvanced", "Less is slower (0: Default)", None))
        self.install_prereqs_label.setText(QCoreApplication.translate("InstallDialogAdvanced", "Install prerequisites", None))
#if QT_CONFIG(tooltip)
        self.install_prereqs_check.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.install_prereqs_check.setText("")
        self.read_files_label.setText(QCoreApplication.translate("InstallDialogAdvanced", "Read from files", None))
#if QT_CONFIG(tooltip)
        self.read_files_check.setToolTip(QCoreApplication.translate("InstallDialogAdvanced", "Read duplicated parts from already saved files, do not keep them in memory.", None))
#endif // QT_CONFIG(tooltip)
        self.read_files_check.setText(QCoreApplication.translate("InstallDialogAdvanced", "Increases storage I/O, reduces RAM usage.", None))
        self.dl_optimizations_label.setText(QCoreApplication.translate("InstallDialogAdvanced", "Enable reordering", None))
#if QT_CONFIG(tooltip)
        self.dl_optimizations_check.setToolTip(QCoreApplication.translate("InstallDialogAdvanced", "Enable reordering optimization to reduce RAM requirements during download (may have adverse results for some titles).", None))
#endif // QT_CONFIG(tooltip)
        self.dl_optimizations_check.setText(QCoreApplication.translate("InstallDialogAdvanced", "May cause issues!", None))
        self.force_download_label.setText(QCoreApplication.translate("InstallDialogAdvanced", "Force redownload", None))
#if QT_CONFIG(tooltip)
        self.force_download_check.setToolTip(QCoreApplication.translate("InstallDialogAdvanced", "Download all files / ignore existing (overwrite).", None))
#endif // QT_CONFIG(tooltip)
        self.force_download_check.setText("")
        self.ignore_space_label.setText(QCoreApplication.translate("InstallDialogAdvanced", "Ignore free space", None))
#if QT_CONFIG(tooltip)
        self.ignore_space_check.setToolTip(QCoreApplication.translate("InstallDialogAdvanced", "Do not abort if not enough free space is available.", None))
#endif // QT_CONFIG(tooltip)
        self.ignore_space_check.setText(QCoreApplication.translate("InstallDialogAdvanced", "Use with caution!", None))
        self.download_only_label.setText(QCoreApplication.translate("InstallDialogAdvanced", "Download only", None))
#if QT_CONFIG(tooltip)
        self.download_only_check.setToolTip(QCoreApplication.translate("InstallDialogAdvanced", "Do not install app and do not run prerequisite installers after download.", None))
#endif // QT_CONFIG(tooltip)
        self.download_only_check.setText(QCoreApplication.translate("InstallDialogAdvanced", "Do not try to install.", None))
    # retranslateUi


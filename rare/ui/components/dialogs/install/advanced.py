# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'advanced.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QCheckBox, QFormLayout, QHBoxLayout, QLabel, QSizePolicy, QSpinBox


class Ui_InstallDialogAdvanced(object):
    def setupUi(self, InstallDialogAdvanced):
        if not InstallDialogAdvanced.objectName():
            InstallDialogAdvanced.setObjectName(u"InstallDialogAdvanced")
        InstallDialogAdvanced.resize(409, 228)
        InstallDialogAdvanced.setWindowTitle(u"InstallDialogAdvanced")
        self.main_layout = QFormLayout(InstallDialogAdvanced)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.max_workers_label = QLabel(InstallDialogAdvanced)
        self.max_workers_label.setObjectName(u"max_workers_label")
        self.max_workers_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.main_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.max_workers_label)

        self.max_workers_layout = QHBoxLayout()
        self.max_workers_layout.setObjectName(u"max_workers_layout")
        self.max_workers_spin = QSpinBox(InstallDialogAdvanced)
        self.max_workers_spin.setObjectName(u"max_workers_spin")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.max_workers_spin.sizePolicy().hasHeightForWidth())
        self.max_workers_spin.setSizePolicy(sizePolicy)

        self.max_workers_layout.addWidget(self.max_workers_spin)

        self.max_workers_info = QLabel(InstallDialogAdvanced)
        self.max_workers_info.setObjectName(u"max_workers_info")
        font = QFont()
        font.setItalic(True)
        self.max_workers_info.setFont(font)

        self.max_workers_layout.addWidget(self.max_workers_info)


        self.main_layout.setLayout(0, QFormLayout.ItemRole.FieldRole, self.max_workers_layout)

        self.max_memory_label = QLabel(InstallDialogAdvanced)
        self.max_memory_label.setObjectName(u"max_memory_label")
        self.max_memory_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.main_layout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.max_memory_label)

        self.max_memory_layout = QHBoxLayout()
        self.max_memory_layout.setObjectName(u"max_memory_layout")
        self.max_memory_spin = QSpinBox(InstallDialogAdvanced)
        self.max_memory_spin.setObjectName(u"max_memory_spin")
        sizePolicy.setHeightForWidth(self.max_memory_spin.sizePolicy().hasHeightForWidth())
        self.max_memory_spin.setSizePolicy(sizePolicy)
        self.max_memory_spin.setMinimum(0)
        self.max_memory_spin.setMaximum(10240)
        self.max_memory_spin.setSingleStep(128)
        self.max_memory_spin.setValue(1024)

        self.max_memory_layout.addWidget(self.max_memory_spin)

        self.max_memory_info = QLabel(InstallDialogAdvanced)
        self.max_memory_info.setObjectName(u"max_memory_info")
        self.max_memory_info.setFont(font)

        self.max_memory_layout.addWidget(self.max_memory_info)


        self.main_layout.setLayout(1, QFormLayout.ItemRole.FieldRole, self.max_memory_layout)

        self.install_prereqs_label = QLabel(InstallDialogAdvanced)
        self.install_prereqs_label.setObjectName(u"install_prereqs_label")

        self.main_layout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.install_prereqs_label)

        self.install_prereqs_check = QCheckBox(InstallDialogAdvanced)
        self.install_prereqs_check.setObjectName(u"install_prereqs_check")
        self.install_prereqs_check.setFont(font)
        self.install_prereqs_check.setChecked(False)

        self.main_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.install_prereqs_check)

        self.dl_optimizations_label = QLabel(InstallDialogAdvanced)
        self.dl_optimizations_label.setObjectName(u"dl_optimizations_label")

        self.main_layout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.dl_optimizations_label)

        self.dl_optimizations_check = QCheckBox(InstallDialogAdvanced)
        self.dl_optimizations_check.setObjectName(u"dl_optimizations_check")
        self.dl_optimizations_check.setFont(font)
        self.dl_optimizations_check.setChecked(False)

        self.main_layout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.dl_optimizations_check)

        self.force_download_label = QLabel(InstallDialogAdvanced)
        self.force_download_label.setObjectName(u"force_download_label")

        self.main_layout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.force_download_label)

        self.force_download_check = QCheckBox(InstallDialogAdvanced)
        self.force_download_check.setObjectName(u"force_download_check")
        self.force_download_check.setFont(font)

        self.main_layout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.force_download_check)

        self.ignore_space_label = QLabel(InstallDialogAdvanced)
        self.ignore_space_label.setObjectName(u"ignore_space_label")

        self.main_layout.setWidget(7, QFormLayout.ItemRole.LabelRole, self.ignore_space_label)

        self.ignore_space_check = QCheckBox(InstallDialogAdvanced)
        self.ignore_space_check.setObjectName(u"ignore_space_check")
        self.ignore_space_check.setFont(font)

        self.main_layout.setWidget(7, QFormLayout.ItemRole.FieldRole, self.ignore_space_check)

        self.download_only_label = QLabel(InstallDialogAdvanced)
        self.download_only_label.setObjectName(u"download_only_label")

        self.main_layout.setWidget(8, QFormLayout.ItemRole.LabelRole, self.download_only_label)

        self.download_only_check = QCheckBox(InstallDialogAdvanced)
        self.download_only_check.setObjectName(u"download_only_check")
        self.download_only_check.setFont(font)

        self.main_layout.setWidget(8, QFormLayout.ItemRole.FieldRole, self.download_only_check)

        self.read_files_label = QLabel(InstallDialogAdvanced)
        self.read_files_label.setObjectName(u"read_files_label")

        self.main_layout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.read_files_label)

        self.read_files_check = QCheckBox(InstallDialogAdvanced)
        self.read_files_check.setObjectName(u"read_files_check")
        self.read_files_check.setFont(font)

        self.main_layout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.read_files_check)

        self.use_signed_urls_label = QLabel(InstallDialogAdvanced)
        self.use_signed_urls_label.setObjectName(u"use_signed_urls_label")

        self.main_layout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.use_signed_urls_label)

        self.use_signed_urls_check = QCheckBox(InstallDialogAdvanced)
        self.use_signed_urls_check.setObjectName(u"use_signed_urls_check")
        self.use_signed_urls_check.setFont(font)

        self.main_layout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.use_signed_urls_check)


        self.retranslateUi(InstallDialogAdvanced)
    # setupUi

    def retranslateUi(self, InstallDialogAdvanced):
        self.max_workers_label.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Max workers", None))
#if QT_CONFIG(tooltip)
        self.max_workers_spin.setToolTip(QCoreApplication.translate("InstallDialogAdvanced", u"Maximum amount of download workers, default: min(2 * CPUs, 16).", None))
#endif // QT_CONFIG(tooltip)
        self.max_workers_info.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Less is slower. (0: Default)", None))
        self.max_memory_label.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Max shared memory", None))
#if QT_CONFIG(tooltip)
        self.max_memory_spin.setToolTip(QCoreApplication.translate("InstallDialogAdvanced", u"Maximum amount of shared memory to use (in MiB), default: 1 GiB.", None))
#endif // QT_CONFIG(tooltip)
        self.max_memory_spin.setSuffix(QCoreApplication.translate("InstallDialogAdvanced", u"MiB", None))
        self.max_memory_info.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Less is slower (0: Default)", None))
        self.install_prereqs_label.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Install prerequisites", None))
#if QT_CONFIG(tooltip)
        self.install_prereqs_check.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.install_prereqs_check.setText("")
        self.dl_optimizations_label.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Enable reordering", None))
#if QT_CONFIG(tooltip)
        self.dl_optimizations_check.setToolTip(QCoreApplication.translate("InstallDialogAdvanced", u"Enable reordering optimization to reduce RAM requirements during download (may have adverse results for some titles).", None))
#endif // QT_CONFIG(tooltip)
        self.dl_optimizations_check.setText(QCoreApplication.translate("InstallDialogAdvanced", u"May cause issues!", None))
        self.force_download_label.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Force redownload", None))
#if QT_CONFIG(tooltip)
        self.force_download_check.setToolTip(QCoreApplication.translate("InstallDialogAdvanced", u"Download all files / ignore existing (overwrite).", None))
#endif // QT_CONFIG(tooltip)
        self.force_download_check.setText("")
        self.ignore_space_label.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Ignore free space", None))
#if QT_CONFIG(tooltip)
        self.ignore_space_check.setToolTip(QCoreApplication.translate("InstallDialogAdvanced", u"Do not abort if not enough free space is available.", None))
#endif // QT_CONFIG(tooltip)
        self.ignore_space_check.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Use with caution!", None))
        self.download_only_label.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Download only", None))
#if QT_CONFIG(tooltip)
        self.download_only_check.setToolTip(QCoreApplication.translate("InstallDialogAdvanced", u"Do not install app and do not run prerequisite installers after download.", None))
#endif // QT_CONFIG(tooltip)
        self.download_only_check.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Do not try to install.", None))
        self.read_files_label.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Read from files", None))
#if QT_CONFIG(tooltip)
        self.read_files_check.setToolTip(QCoreApplication.translate("InstallDialogAdvanced", u"Read duplicated parts from already saved files, do not keep them in memory.", None))
#endif // QT_CONFIG(tooltip)
        self.read_files_check.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Increases storage I/O, reduces RAM usage.", None))
        self.use_signed_urls_label.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Use signed URLs", None))
#if QT_CONFIG(tooltip)
        self.use_signed_urls_check.setToolTip(QCoreApplication.translate("InstallDialogAdvanced", u"Always use signed chunk URLs, even if the Epic API indicates not to.", None))
#endif // QT_CONFIG(tooltip)
        self.use_signed_urls_check.setText("")
        pass
    # retranslateUi


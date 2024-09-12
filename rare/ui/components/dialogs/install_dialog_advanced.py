# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'install_dialog_advanced.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QFormLayout, QHBoxLayout,
    QLabel, QSizePolicy, QSpinBox, QWidget)

class Ui_InstallDialogAdvanced(object):
    def setupUi(self, InstallDialogAdvanced):
        if not InstallDialogAdvanced.objectName():
            InstallDialogAdvanced.setObjectName(u"InstallDialogAdvanced")
        InstallDialogAdvanced.resize(379, 208)
        InstallDialogAdvanced.setWindowTitle(u"InstallDialogAdvanced")
        self.install_dialog_advanced_layout = QFormLayout(InstallDialogAdvanced)
        self.install_dialog_advanced_layout.setObjectName(u"install_dialog_advanced_layout")
        self.max_workers_label = QLabel(InstallDialogAdvanced)
        self.max_workers_label.setObjectName(u"max_workers_label")
        self.max_workers_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.install_dialog_advanced_layout.setWidget(0, QFormLayout.LabelRole, self.max_workers_label)

        self.max_workers_layout = QHBoxLayout()
        self.max_workers_layout.setObjectName(u"max_workers_layout")
        self.max_workers_spin = QSpinBox(InstallDialogAdvanced)
        self.max_workers_spin.setObjectName(u"max_workers_spin")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
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


        self.install_dialog_advanced_layout.setLayout(0, QFormLayout.ItemRole.FieldRole, self.max_workers_layout)

        self.max_memory_label = QLabel(InstallDialogAdvanced)
        self.max_memory_label.setObjectName(u"max_memory_label")
        self.max_memory_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.install_dialog_advanced_layout.setWidget(1, QFormLayout.LabelRole, self.max_memory_label)

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


        self.install_dialog_advanced_layout.setLayout(1, QFormLayout.ItemRole.FieldRole, self.max_memory_layout)

        self.install_prereqs_label = QLabel(InstallDialogAdvanced)
        self.install_prereqs_label.setObjectName(u"install_prereqs_label")

        self.install_dialog_advanced_layout.setWidget(2, QFormLayout.LabelRole, self.install_prereqs_label)

        self.install_prereqs_check = QCheckBox(InstallDialogAdvanced)
        self.install_prereqs_check.setObjectName(u"install_prereqs_check")
        self.install_prereqs_check.setFont(font)
        self.install_prereqs_check.setText(u"")
        self.install_prereqs_check.setChecked(False)

        self.install_dialog_advanced_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.install_prereqs_check)

        self.dl_optimizations_label = QLabel(InstallDialogAdvanced)
        self.dl_optimizations_label.setObjectName(u"dl_optimizations_label")

        self.install_dialog_advanced_layout.setWidget(3, QFormLayout.LabelRole, self.dl_optimizations_label)

        self.dl_optimizations_check = QCheckBox(InstallDialogAdvanced)
        self.dl_optimizations_check.setObjectName(u"dl_optimizations_check")
        self.dl_optimizations_check.setText(u"")
        self.dl_optimizations_check.setChecked(False)

        self.install_dialog_advanced_layout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.dl_optimizations_check)

        self.force_download_label = QLabel(InstallDialogAdvanced)
        self.force_download_label.setObjectName(u"force_download_label")

        self.install_dialog_advanced_layout.setWidget(4, QFormLayout.LabelRole, self.force_download_label)

        self.force_download_check = QCheckBox(InstallDialogAdvanced)
        self.force_download_check.setObjectName(u"force_download_check")
        self.force_download_check.setText(u"")

        self.install_dialog_advanced_layout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.force_download_check)

        self.ignore_space_label = QLabel(InstallDialogAdvanced)
        self.ignore_space_label.setObjectName(u"ignore_space_label")

        self.install_dialog_advanced_layout.setWidget(5, QFormLayout.LabelRole, self.ignore_space_label)

        self.ignore_space_check = QCheckBox(InstallDialogAdvanced)
        self.ignore_space_check.setObjectName(u"ignore_space_check")
        self.ignore_space_check.setFont(font)

        self.install_dialog_advanced_layout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.ignore_space_check)

        self.download_only_label = QLabel(InstallDialogAdvanced)
        self.download_only_label.setObjectName(u"download_only_label")

        self.install_dialog_advanced_layout.setWidget(6, QFormLayout.LabelRole, self.download_only_label)

        self.download_only_check = QCheckBox(InstallDialogAdvanced)
        self.download_only_check.setObjectName(u"download_only_check")
        self.download_only_check.setFont(font)

        self.install_dialog_advanced_layout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.download_only_check)


        self.retranslateUi(InstallDialogAdvanced)
    # setupUi

    def retranslateUi(self, InstallDialogAdvanced):
        self.max_workers_label.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Max workers", None))
        self.max_workers_info.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Less is slower. (0: Default)", None))
        self.max_memory_label.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Max shared memory", None))
        self.max_memory_spin.setSuffix(QCoreApplication.translate("InstallDialogAdvanced", u"MiB", None))
        self.max_memory_info.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Less is slower (0: Default)", None))
        self.install_prereqs_label.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Install prerequisites", None))
        self.dl_optimizations_label.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Enable reordering", None))
        self.force_download_label.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Force redownload", None))
        self.ignore_space_label.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Ignore free space", None))
        self.ignore_space_check.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Use with caution!", None))
        self.download_only_label.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Download only", None))
        self.download_only_check.setText(QCoreApplication.translate("InstallDialogAdvanced", u"Do not try to install.", None))
        pass
    # retranslateUi


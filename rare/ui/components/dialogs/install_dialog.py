# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'install_dialog.ui'
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
    QFrame, QLabel, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_InstallDialog(object):
    def setupUi(self, InstallDialog):
        if not InstallDialog.objectName():
            InstallDialog.setObjectName(u"InstallDialog")
        InstallDialog.resize(197, 195)
        InstallDialog.setWindowTitle(u"InstallDialog")
        self.main_layout = QFormLayout(InstallDialog)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.install_dir_label = QLabel(InstallDialog)
        self.install_dir_label.setObjectName(u"install_dir_label")

        self.main_layout.setWidget(0, QFormLayout.LabelRole, self.install_dir_label)

        self.platform_label = QLabel(InstallDialog)
        self.platform_label.setObjectName(u"platform_label")

        self.main_layout.setWidget(1, QFormLayout.LabelRole, self.platform_label)

        self.platform_combo = QComboBox(InstallDialog)
        self.platform_combo.setObjectName(u"platform_combo")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.platform_combo.sizePolicy().hasHeightForWidth())
        self.platform_combo.setSizePolicy(sizePolicy)

        self.main_layout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.platform_combo)

        self.shortcut_label = QLabel(InstallDialog)
        self.shortcut_label.setObjectName(u"shortcut_label")
        self.shortcut_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.main_layout.setWidget(2, QFormLayout.LabelRole, self.shortcut_label)

        self.shortcut_check = QCheckBox(InstallDialog)
        self.shortcut_check.setObjectName(u"shortcut_check")
        self.shortcut_check.setText(u"")

        self.main_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.shortcut_check)

        self.selectable_layout = QVBoxLayout()
        self.selectable_layout.setObjectName(u"selectable_layout")

        self.main_layout.setLayout(3, QFormLayout.SpanningRole, self.selectable_layout)

        self.advanced_layout = QVBoxLayout()
        self.advanced_layout.setObjectName(u"advanced_layout")

        self.main_layout.setLayout(4, QFormLayout.SpanningRole, self.advanced_layout)

        self.download_size_label = QLabel(InstallDialog)
        self.download_size_label.setObjectName(u"download_size_label")

        self.main_layout.setWidget(5, QFormLayout.LabelRole, self.download_size_label)

        self.download_size_text = QLabel(InstallDialog)
        self.download_size_text.setObjectName(u"download_size_text")
        font = QFont()
        font.setItalic(True)
        self.download_size_text.setFont(font)

        self.main_layout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.download_size_text)

        self.install_size_label = QLabel(InstallDialog)
        self.install_size_label.setObjectName(u"install_size_label")

        self.main_layout.setWidget(6, QFormLayout.LabelRole, self.install_size_label)

        self.install_size_text = QLabel(InstallDialog)
        self.install_size_text.setObjectName(u"install_size_text")
        self.install_size_text.setFont(font)
        self.install_size_text.setWordWrap(True)

        self.main_layout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.install_size_text)

        self.avail_space_label = QLabel(InstallDialog)
        self.avail_space_label.setObjectName(u"avail_space_label")

        self.main_layout.setWidget(7, QFormLayout.LabelRole, self.avail_space_label)

        self.avail_space = QLabel(InstallDialog)
        self.avail_space.setObjectName(u"avail_space")
        font1 = QFont()
        font1.setBold(True)
        self.avail_space.setFont(font1)

        self.main_layout.setWidget(7, QFormLayout.ItemRole.FieldRole, self.avail_space)

        self.warning_label = QLabel(InstallDialog)
        self.warning_label.setObjectName(u"warning_label")

        self.main_layout.setWidget(8, QFormLayout.LabelRole, self.warning_label)

        self.warning_text = QLabel(InstallDialog)
        self.warning_text.setObjectName(u"warning_text")
        self.warning_text.setFont(font)
        self.warning_text.setFrameShape(QFrame.Shape.StyledPanel)
        self.warning_text.setFrameShadow(QFrame.Sunken)
        self.warning_text.setWordWrap(True)
        self.warning_text.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.main_layout.setWidget(8, QFormLayout.ItemRole.FieldRole, self.warning_text)


        self.retranslateUi(InstallDialog)
    # setupUi

    def retranslateUi(self, InstallDialog):
        self.install_dir_label.setText(QCoreApplication.translate("InstallDialog", u"Install folder", None))
        self.platform_label.setText(QCoreApplication.translate("InstallDialog", u"Platform", None))
        self.shortcut_label.setText(QCoreApplication.translate("InstallDialog", u"Create shortcut", None))
        self.download_size_label.setText(QCoreApplication.translate("InstallDialog", u"Download size", None))
        self.download_size_text.setText(QCoreApplication.translate("InstallDialog", u"Click verify...", None))
        self.install_size_label.setText(QCoreApplication.translate("InstallDialog", u"Total install size", None))
        self.install_size_text.setText(QCoreApplication.translate("InstallDialog", u"Click verify...", None))
        self.avail_space_label.setText(QCoreApplication.translate("InstallDialog", u"Available space", None))
        self.avail_space.setText("")
        self.warning_label.setText(QCoreApplication.translate("InstallDialog", u"Warning", None))
        self.warning_text.setText(QCoreApplication.translate("InstallDialog", u"None", None))
        pass
    # retranslateUi


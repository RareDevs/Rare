# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'egl_sync_group.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QFormLayout, QGroupBox,
    QLabel, QSizePolicy, QVBoxLayout, QWidget)

class Ui_EGLSyncGroup(object):
    def setupUi(self, EGLSyncGroup):
        if not EGLSyncGroup.objectName():
            EGLSyncGroup.setObjectName(u"EGLSyncGroup")
        EGLSyncGroup.resize(424, 106)
        EGLSyncGroup.setWindowTitle(u"EGLSyncGroup")
        EGLSyncGroup.setCheckable(False)
        EGLSyncGroup.setChecked(False)
        self.egl_sync_layout = QFormLayout(EGLSyncGroup)
        self.egl_sync_layout.setObjectName(u"egl_sync_layout")
        self.egl_sync_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.egl_path_edit_label = QLabel(EGLSyncGroup)
        self.egl_path_edit_label.setObjectName(u"egl_path_edit_label")

        self.egl_sync_layout.setWidget(0, QFormLayout.LabelRole, self.egl_path_edit_label)

        self.egl_sync_check_label = QLabel(EGLSyncGroup)
        self.egl_sync_check_label.setObjectName(u"egl_sync_check_label")

        self.egl_sync_layout.setWidget(2, QFormLayout.LabelRole, self.egl_sync_check_label)

        self.egl_sync_check = QCheckBox(EGLSyncGroup)
        self.egl_sync_check.setObjectName(u"egl_sync_check")
        font = QFont()
        font.setItalic(True)
        self.egl_sync_check.setFont(font)

        self.egl_sync_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.egl_sync_check)

        self.import_export_layout = QVBoxLayout()
        self.import_export_layout.setObjectName(u"import_export_layout")

        self.egl_sync_layout.setLayout(3, QFormLayout.SpanningRole, self.import_export_layout)

        self.egl_path_info_label = QLabel(EGLSyncGroup)
        self.egl_path_info_label.setObjectName(u"egl_path_info_label")

        self.egl_sync_layout.setWidget(1, QFormLayout.LabelRole, self.egl_path_info_label)


        self.retranslateUi(EGLSyncGroup)
    # setupUi

    def retranslateUi(self, EGLSyncGroup):
        EGLSyncGroup.setTitle(QCoreApplication.translate("EGLSyncGroup", u"Sync with Epic Games Launcher", None))
        self.egl_path_edit_label.setText(QCoreApplication.translate("EGLSyncGroup", u"Manifest path", None))
        self.egl_sync_check_label.setText(QCoreApplication.translate("EGLSyncGroup", u"Enable automatic sync", None))
        self.egl_sync_check.setText(QCoreApplication.translate("EGLSyncGroup", u"This will immediately synchronize with EGL", None))
        self.egl_path_info_label.setText(QCoreApplication.translate("EGLSyncGroup", u"Estimated path", None))
    # retranslateUi


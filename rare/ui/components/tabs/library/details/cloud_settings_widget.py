# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'cloud_settings_widget.ui'
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
    QLabel, QSizePolicy, QWidget)

class Ui_CloudSettingsWidget(object):
    def setupUi(self, CloudSettingsWidget):
        if not CloudSettingsWidget.objectName():
            CloudSettingsWidget.setObjectName(u"CloudSettingsWidget")
        CloudSettingsWidget.resize(388, 78)
        CloudSettingsWidget.setWindowTitle(u"CloudSettingsWidget")
        self.main_layout = QFormLayout(CloudSettingsWidget)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.sync_label = QLabel(CloudSettingsWidget)
        self.sync_label.setObjectName(u"sync_label")

        self.main_layout.setWidget(0, QFormLayout.LabelRole, self.sync_label)

        self.sync_check = QCheckBox(CloudSettingsWidget)
        self.sync_check.setObjectName(u"sync_check")
        font = QFont()
        font.setItalic(True)
        self.sync_check.setFont(font)
        self.sync_check.setText(u"Automatically synchronize saves with the cloud")

        self.main_layout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.sync_check)

        self.path_label = QLabel(CloudSettingsWidget)
        self.path_label.setObjectName(u"path_label")

        self.main_layout.setWidget(1, QFormLayout.LabelRole, self.path_label)


        self.retranslateUi(CloudSettingsWidget)
    # setupUi

    def retranslateUi(self, CloudSettingsWidget):
        CloudSettingsWidget.setTitle(QCoreApplication.translate("CloudSettingsWidget", u"Settings", None))
        self.sync_label.setText(QCoreApplication.translate("CloudSettingsWidget", u"Enable sync", None))
        self.path_label.setText(QCoreApplication.translate("CloudSettingsWidget", u"Saves path", None))
    # retranslateUi


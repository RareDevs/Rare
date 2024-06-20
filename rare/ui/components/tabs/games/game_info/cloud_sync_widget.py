# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'cloud_sync_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_CloudSyncWidget(object):
    def setupUi(self, CloudSyncWidget):
        if not CloudSyncWidget.objectName():
            CloudSyncWidget.setObjectName(u"CloudSyncWidget")
        CloudSyncWidget.resize(438, 137)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(CloudSyncWidget.sizePolicy().hasHeightForWidth())
        CloudSyncWidget.setSizePolicy(sizePolicy)
        CloudSyncWidget.setWindowTitle(u"SyncWidget")
        self.main_layout = QHBoxLayout(CloudSyncWidget)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.local_group = QGroupBox(CloudSyncWidget)
        self.local_group.setObjectName(u"local_group")
        self.local_layout = QVBoxLayout(self.local_group)
        self.local_layout.setObjectName(u"local_layout")
        self.date_info_local = QLabel(self.local_group)
        self.date_info_local.setObjectName(u"date_info_local")
        self.date_info_local.setText(u"")
        self.date_info_local.setAlignment(Qt.AlignCenter)

        self.local_layout.addWidget(self.date_info_local)

        self.icon_local = QLabel(self.local_group)
        self.icon_local.setObjectName(u"icon_local")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.icon_local.sizePolicy().hasHeightForWidth())
        self.icon_local.setSizePolicy(sizePolicy1)
        self.icon_local.setText(u"")
        self.icon_local.setAlignment(Qt.AlignCenter)

        self.local_layout.addWidget(self.icon_local)

        self.age_label_local = QLabel(self.local_group)
        self.age_label_local.setObjectName(u"age_label_local")
        self.age_label_local.setAlignment(Qt.AlignCenter)

        self.local_layout.addWidget(self.age_label_local)

        self.upload_button = QPushButton(self.local_group)
        self.upload_button.setObjectName(u"upload_button")
        self.upload_button.setMinimumSize(QSize(192, 0))

        self.local_layout.addWidget(self.upload_button)


        self.main_layout.addWidget(self.local_group)

        self.cloud_group = QGroupBox(CloudSyncWidget)
        self.cloud_group.setObjectName(u"cloud_group")
        self.cloud_layout = QVBoxLayout(self.cloud_group)
        self.cloud_layout.setObjectName(u"cloud_layout")
        self.date_info_remote = QLabel(self.cloud_group)
        self.date_info_remote.setObjectName(u"date_info_remote")
        self.date_info_remote.setText(u"")
        self.date_info_remote.setAlignment(Qt.AlignCenter)

        self.cloud_layout.addWidget(self.date_info_remote)

        self.icon_remote = QLabel(self.cloud_group)
        self.icon_remote.setObjectName(u"icon_remote")
        sizePolicy1.setHeightForWidth(self.icon_remote.sizePolicy().hasHeightForWidth())
        self.icon_remote.setSizePolicy(sizePolicy1)
        self.icon_remote.setText(u"")
        self.icon_remote.setAlignment(Qt.AlignCenter)

        self.cloud_layout.addWidget(self.icon_remote)

        self.age_label_remote = QLabel(self.cloud_group)
        self.age_label_remote.setObjectName(u"age_label_remote")
        self.age_label_remote.setText(u"")
        self.age_label_remote.setAlignment(Qt.AlignCenter)

        self.cloud_layout.addWidget(self.age_label_remote)

        self.download_button = QPushButton(self.cloud_group)
        self.download_button.setObjectName(u"download_button")
        self.download_button.setMinimumSize(QSize(192, 0))

        self.cloud_layout.addWidget(self.download_button)


        self.main_layout.addWidget(self.cloud_group)


        self.retranslateUi(CloudSyncWidget)
    # setupUi

    def retranslateUi(self, CloudSyncWidget):
        self.local_group.setTitle(QCoreApplication.translate("CloudSyncWidget", u"Local", None))
        self.age_label_local.setText("")
        self.upload_button.setText(QCoreApplication.translate("CloudSyncWidget", u"Upload", None))
        self.cloud_group.setTitle(QCoreApplication.translate("CloudSyncWidget", u"Cloud", None))
        self.download_button.setText(QCoreApplication.translate("CloudSyncWidget", u"Download", None))
        pass
    # retranslateUi


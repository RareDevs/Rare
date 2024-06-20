# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'queue_info_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QLabel, QLayout,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_QueueInfoWidget(object):
    def setupUi(self, QueueInfoWidget):
        if not QueueInfoWidget.objectName():
            QueueInfoWidget.setObjectName(u"QueueInfoWidget")
        QueueInfoWidget.resize(624, 60)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(QueueInfoWidget.sizePolicy().hasHeightForWidth())
        QueueInfoWidget.setSizePolicy(sizePolicy)
        QueueInfoWidget.setWindowTitle(u"QueueInfoWidget")
        self.queue_info_layout = QGridLayout(QueueInfoWidget)
        self.queue_info_layout.setObjectName(u"queue_info_layout")
        self.queue_info_layout.setContentsMargins(0, 0, 0, 0)
        self.dl_size_label = QLabel(QueueInfoWidget)
        self.dl_size_label.setObjectName(u"dl_size_label")
        font = QFont()
        font.setBold(True)
        self.dl_size_label.setFont(font)
        self.dl_size_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.queue_info_layout.addWidget(self.dl_size_label, 1, 3, 1, 1)

        self.title = QLabel(QueueInfoWidget)
        self.title.setObjectName(u"title")
        self.title.setFont(font)
        self.title.setText(u"title")

        self.queue_info_layout.addWidget(self.title, 0, 1, 1, 4)

        self.local_version_label = QLabel(QueueInfoWidget)
        self.local_version_label.setObjectName(u"local_version_label")
        self.local_version_label.setFont(font)
        self.local_version_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.queue_info_layout.addWidget(self.local_version_label, 2, 1, 1, 1)

        self.image_layout = QVBoxLayout()
        self.image_layout.setObjectName(u"image_layout")
        self.image_layout.setSizeConstraint(QLayout.SetFixedSize)

        self.queue_info_layout.addLayout(self.image_layout, 0, 0, 3, 1)

        self.install_size_label = QLabel(QueueInfoWidget)
        self.install_size_label.setObjectName(u"install_size_label")
        self.install_size_label.setFont(font)
        self.install_size_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.queue_info_layout.addWidget(self.install_size_label, 2, 3, 1, 1)

        self.install_size = QLabel(QueueInfoWidget)
        self.install_size.setObjectName(u"install_size")
        self.install_size.setMinimumSize(QSize(160, 0))
        self.install_size.setText(u"install_size")

        self.queue_info_layout.addWidget(self.install_size, 2, 4, 1, 1)

        self.info_hspacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.queue_info_layout.addItem(self.info_hspacer, 0, 5, 3, 1)

        self.dl_size = QLabel(QueueInfoWidget)
        self.dl_size.setObjectName(u"dl_size")
        self.dl_size.setMinimumSize(QSize(160, 0))
        self.dl_size.setText(u"dl_size")

        self.queue_info_layout.addWidget(self.dl_size, 1, 4, 1, 1)

        self.remote_version_label = QLabel(QueueInfoWidget)
        self.remote_version_label.setObjectName(u"remote_version_label")
        self.remote_version_label.setFont(font)
        self.remote_version_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.queue_info_layout.addWidget(self.remote_version_label, 1, 1, 1, 1)

        self.local_version = QLabel(QueueInfoWidget)
        self.local_version.setObjectName(u"local_version")
        self.local_version.setMinimumSize(QSize(160, 0))
        self.local_version.setMaximumSize(QSize(160, 16777215))
        self.local_version.setText(u"local_version")

        self.queue_info_layout.addWidget(self.local_version, 2, 2, 1, 1)

        self.remote_version = QLabel(QueueInfoWidget)
        self.remote_version.setObjectName(u"remote_version")
        self.remote_version.setMinimumSize(QSize(160, 0))
        self.remote_version.setMaximumSize(QSize(160, 16777215))
        self.remote_version.setText(u"remote_version")

        self.queue_info_layout.addWidget(self.remote_version, 1, 2, 1, 1)


        self.retranslateUi(QueueInfoWidget)
    # setupUi

    def retranslateUi(self, QueueInfoWidget):
        self.dl_size_label.setText(QCoreApplication.translate("QueueInfoWidget", u"Download size", None))
        self.local_version_label.setText(QCoreApplication.translate("QueueInfoWidget", u"Local version", None))
        self.install_size_label.setText(QCoreApplication.translate("QueueInfoWidget", u"Installed size", None))
        self.remote_version_label.setText(QCoreApplication.translate("QueueInfoWidget", u"Remote version", None))
        pass
    # retranslateUi


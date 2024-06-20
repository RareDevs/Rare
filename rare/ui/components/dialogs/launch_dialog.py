# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'launch_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QLabel, QProgressBar,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_LaunchDialog(object):
    def setupUi(self, LaunchDialog):
        if not LaunchDialog.objectName():
            LaunchDialog.setObjectName(u"LaunchDialog")
        LaunchDialog.resize(400, 160)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(LaunchDialog.sizePolicy().hasHeightForWidth())
        LaunchDialog.setSizePolicy(sizePolicy)
        LaunchDialog.setMinimumSize(QSize(400, 160))
        LaunchDialog.setMaximumSize(QSize(400, 160))
        self.launch_layout = QVBoxLayout(LaunchDialog)
        self.launch_layout.setObjectName(u"launch_layout")
        self.title_label = QLabel(LaunchDialog)
        self.title_label.setObjectName(u"title_label")

        self.launch_layout.addWidget(self.title_label)

        self.progress_bar = QProgressBar(LaunchDialog)
        self.progress_bar.setObjectName(u"progress_bar")
        self.progress_bar.setValue(0)

        self.launch_layout.addWidget(self.progress_bar)


        self.retranslateUi(LaunchDialog)
    # setupUi

    def retranslateUi(self, LaunchDialog):
        LaunchDialog.setWindowTitle(QCoreApplication.translate("LaunchDialog", u"Launching", None))
        self.title_label.setText(QCoreApplication.translate("LaunchDialog", u"<h2>Launching Rare</h2>", None))
    # retranslateUi


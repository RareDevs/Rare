# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'queue_base_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_QueueBaseWidget(object):
    def setupUi(self, QueueBaseWidget):
        if not QueueBaseWidget.objectName():
            QueueBaseWidget.setObjectName(u"QueueBaseWidget")
        QueueBaseWidget.resize(380, 62)
        QueueBaseWidget.setWindowTitle(u"QueueBaseWidget")
        QueueBaseWidget.setFrameShape(QFrame.Shape.StyledPanel)
        self.queue_base_layout = QHBoxLayout(QueueBaseWidget)
        self.queue_base_layout.setObjectName(u"queue_base_layout")
        self.queue_base_layout.setContentsMargins(0, 0, 0, 0)
        self.info_layout = QHBoxLayout()
        self.info_layout.setObjectName(u"info_layout")

        self.queue_base_layout.addLayout(self.info_layout)

        self.move_buttons = QWidget(QueueBaseWidget)
        self.move_buttons.setObjectName(u"move_buttons")
        self.move_buttons_layout = QVBoxLayout(self.move_buttons)
        self.move_buttons_layout.setObjectName(u"move_buttons_layout")
        self.move_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.move_up_button = QPushButton(self.move_buttons)
        self.move_up_button.setObjectName(u"move_up_button")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.move_up_button.sizePolicy().hasHeightForWidth())
        self.move_up_button.setSizePolicy(sizePolicy)
        self.move_up_button.setText(u"")
        self.move_up_button.setProperty("isSquare", 1)

        self.move_buttons_layout.addWidget(self.move_up_button, 0, Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.move_down_button = QPushButton(self.move_buttons)
        self.move_down_button.setObjectName(u"move_down_button")
        sizePolicy.setHeightForWidth(self.move_down_button.sizePolicy().hasHeightForWidth())
        self.move_down_button.setSizePolicy(sizePolicy)
        self.move_down_button.setText(u"")
        self.move_down_button.setProperty("isSquare", 1)

        self.move_buttons_layout.addWidget(self.move_down_button, 0, Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignBottom)


        self.queue_base_layout.addWidget(self.move_buttons)

        self.queue_buttons = QWidget(QueueBaseWidget)
        self.queue_buttons.setObjectName(u"queue_buttons")
        self.queue_buttons_layout = QVBoxLayout(self.queue_buttons)
        self.queue_buttons_layout.setObjectName(u"queue_buttons_layout")
        self.queue_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.force_button = QPushButton(self.queue_buttons)
        self.force_button.setObjectName(u"force_button")

        self.queue_buttons_layout.addWidget(self.force_button)

        self.remove_button = QPushButton(self.queue_buttons)
        self.remove_button.setObjectName(u"remove_button")

        self.queue_buttons_layout.addWidget(self.remove_button, 0, Qt.AlignmentFlag.AlignBottom)


        self.queue_base_layout.addWidget(self.queue_buttons)

        self.update_buttons = QWidget(QueueBaseWidget)
        self.update_buttons.setObjectName(u"update_buttons")
        self.update_buttons_layout = QVBoxLayout(self.update_buttons)
        self.update_buttons_layout.setObjectName(u"update_buttons_layout")
        self.update_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.update_button = QPushButton(self.update_buttons)
        self.update_button.setObjectName(u"update_button")

        self.update_buttons_layout.addWidget(self.update_button)

        self.settings_button = QPushButton(self.update_buttons)
        self.settings_button.setObjectName(u"settings_button")

        self.update_buttons_layout.addWidget(self.settings_button, 0, Qt.AlignmentFlag.AlignBottom)


        self.queue_base_layout.addWidget(self.update_buttons)

        self.queue_base_layout.setStretch(0, 1)

        self.retranslateUi(QueueBaseWidget)
    # setupUi

    def retranslateUi(self, QueueBaseWidget):
        self.force_button.setText(QCoreApplication.translate("QueueBaseWidget", u"Download now", None))
        self.remove_button.setText(QCoreApplication.translate("QueueBaseWidget", u"Remove from queue", None))
        self.update_button.setText(QCoreApplication.translate("QueueBaseWidget", u"Update game", None))
        self.settings_button.setText(QCoreApplication.translate("QueueBaseWidget", u"Update with settings", None))
        pass
    # retranslateUi


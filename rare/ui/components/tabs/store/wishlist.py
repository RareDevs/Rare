# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'wishlist.ui'
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
from PySide6.QtWidgets import (QAbstractScrollArea, QApplication, QCheckBox, QComboBox,
    QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_Wishlist(object):
    def setupUi(self, Wishlist):
        if not Wishlist.objectName():
            Wishlist.setObjectName(u"Wishlist")
        Wishlist.resize(489, 165)
        Wishlist.setWindowTitle(u"Wishlist")
        self.main_layout = QVBoxLayout(Wishlist)
        self.main_layout.setObjectName(u"main_layout")
        self.tool_layout = QHBoxLayout()
        self.tool_layout.setObjectName(u"tool_layout")
        self.filter_combo = QComboBox(Wishlist)
        self.filter_combo.setObjectName(u"filter_combo")

        self.tool_layout.addWidget(self.filter_combo)

        self.order_combo = QComboBox(Wishlist)
        self.order_combo.setObjectName(u"order_combo")

        self.tool_layout.addWidget(self.order_combo)

        self.reverse_check = QCheckBox(Wishlist)
        self.reverse_check.setObjectName(u"reverse_check")

        self.tool_layout.addWidget(self.reverse_check)

        self.hspacer_left = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.tool_layout.addItem(self.hspacer_left)

        self.reload_button = QPushButton(Wishlist)
        self.reload_button.setObjectName(u"reload_button")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.reload_button.sizePolicy().hasHeightForWidth())
        self.reload_button.setSizePolicy(sizePolicy)

        self.tool_layout.addWidget(self.reload_button)


        self.main_layout.addLayout(self.tool_layout)

        self.scrollarea = QScrollArea(Wishlist)
        self.scrollarea.setObjectName(u"scrollarea")
        self.scrollarea.setSizeAdjustPolicy(QScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.scrollarea.setWidgetResizable(True)
        self.container = QWidget()
        self.container.setObjectName(u"container")
        self.container.setGeometry(QRect(0, 0, 473, 115))
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setObjectName(u"container_layout")
        self.no_games_label = QLabel(self.container)
        self.no_games_label.setObjectName(u"no_games_label")

        self.container_layout.addWidget(self.no_games_label, 0, Qt.AlignmentFlag.AlignTop)

        self.scrollarea.setWidget(self.container)

        self.main_layout.addWidget(self.scrollarea)


        self.retranslateUi(Wishlist)
    # setupUi

    def retranslateUi(self, Wishlist):
        self.reverse_check.setText(QCoreApplication.translate("Wishlist", u"Reverse", None))
        self.reload_button.setText("")
        self.no_games_label.setText(QCoreApplication.translate("Wishlist", u"No games matching your filter", None))
        pass
    # retranslateUi


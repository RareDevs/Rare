# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'search.ui'
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
from PySide6.QtWidgets import (QAbstractScrollArea, QApplication, QCheckBox, QFrame,
    QGroupBox, QHBoxLayout, QPushButton, QRadioButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

class Ui_SearchWidget(object):
    def setupUi(self, SearchWidget):
        if not SearchWidget.objectName():
            SearchWidget.setObjectName(u"SearchWidget")
        SearchWidget.resize(491, 382)
        SearchWidget.setWindowTitle(u"SearchWidget")
        self.main_layout = QHBoxLayout(SearchWidget)
        self.main_layout.setObjectName(u"main_layout")
        self.left_layout = QVBoxLayout()
        self.left_layout.setObjectName(u"left_layout")

        self.main_layout.addLayout(self.left_layout)

        self.right_layout = QVBoxLayout()
        self.right_layout.setObjectName(u"right_layout")
        self.reset_button = QPushButton(SearchWidget)
        self.reset_button.setObjectName(u"reset_button")

        self.right_layout.addWidget(self.reset_button)

        self.filter_scrollarea = QScrollArea(SearchWidget)
        self.filter_scrollarea.setObjectName(u"filter_scrollarea")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.filter_scrollarea.sizePolicy().hasHeightForWidth())
        self.filter_scrollarea.setSizePolicy(sizePolicy)
        self.filter_scrollarea.setFrameShape(QFrame.Shape.NoFrame)
        self.filter_scrollarea.setFrameShadow(QFrame.Shadow.Plain)
        self.filter_scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.filter_scrollarea.setSizeAdjustPolicy(QScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.filter_scrollarea.setWidgetResizable(True)
        self.filter_container = QWidget()
        self.filter_container.setObjectName(u"filter_container")
        self.filter_container.setGeometry(QRect(0, 0, 142, 390))
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.filter_container.sizePolicy().hasHeightForWidth())
        self.filter_container.setSizePolicy(sizePolicy1)
        self.filter_container_layout = QVBoxLayout(self.filter_container)
        self.filter_container_layout.setObjectName(u"filter_container_layout")
        self.filter_container_layout.setContentsMargins(0, 0, 3, 0)
        self.price_group = QGroupBox(self.filter_container)
        self.price_group.setObjectName(u"price_group")
        self.price_layout = QVBoxLayout(self.price_group)
        self.price_layout.setObjectName(u"price_layout")
        self.none_price = QRadioButton(self.price_group)
        self.none_price.setObjectName(u"none_price")
        self.none_price.setChecked(True)

        self.price_layout.addWidget(self.none_price)

        self.free_button = QRadioButton(self.price_group)
        self.free_button.setObjectName(u"free_button")

        self.price_layout.addWidget(self.free_button)

        self.under10 = QRadioButton(self.price_group)
        self.under10.setObjectName(u"under10")

        self.price_layout.addWidget(self.under10)

        self.under20 = QRadioButton(self.price_group)
        self.under20.setObjectName(u"under20")

        self.price_layout.addWidget(self.under20)

        self.under30 = QRadioButton(self.price_group)
        self.under30.setObjectName(u"under30")

        self.price_layout.addWidget(self.under30)

        self.above = QRadioButton(self.price_group)
        self.above.setObjectName(u"above")

        self.price_layout.addWidget(self.above)

        self.on_discount = QCheckBox(self.price_group)
        self.on_discount.setObjectName(u"on_discount")

        self.price_layout.addWidget(self.on_discount)


        self.filter_container_layout.addWidget(self.price_group)

        self.platform_group = QGroupBox(self.filter_container)
        self.platform_group.setObjectName(u"platform_group")
        self.platfrom_layout = QVBoxLayout(self.platform_group)
        self.platfrom_layout.setObjectName(u"platfrom_layout")

        self.filter_container_layout.addWidget(self.platform_group)

        self.genre_group = QGroupBox(self.filter_container)
        self.genre_group.setObjectName(u"genre_group")
        self.genre_layout = QVBoxLayout(self.genre_group)
        self.genre_layout.setObjectName(u"genre_layout")

        self.filter_container_layout.addWidget(self.genre_group)

        self.type_group = QGroupBox(self.filter_container)
        self.type_group.setObjectName(u"type_group")
        self.type_layout = QVBoxLayout(self.type_group)
        self.type_layout.setObjectName(u"type_layout")

        self.filter_container_layout.addWidget(self.type_group)

        self.others_group = QGroupBox(self.filter_container)
        self.others_group.setObjectName(u"others_group")
        self.others_layout = QVBoxLayout(self.others_group)
        self.others_layout.setObjectName(u"others_layout")

        self.filter_container_layout.addWidget(self.others_group)

        self.filter_scrollarea.setWidget(self.filter_container)

        self.right_layout.addWidget(self.filter_scrollarea)


        self.main_layout.addLayout(self.right_layout)

        self.main_layout.setStretch(0, 1)

        self.retranslateUi(SearchWidget)
    # setupUi

    def retranslateUi(self, SearchWidget):
        self.reset_button.setText(QCoreApplication.translate("SearchWidget", u"Reset filters", None))
        self.price_group.setTitle(QCoreApplication.translate("SearchWidget", u"Price", None))
        self.none_price.setText(QCoreApplication.translate("SearchWidget", u"None", None))
        self.free_button.setText(QCoreApplication.translate("SearchWidget", u"Free", None))
        self.under10.setText(QCoreApplication.translate("SearchWidget", u"Under 10", None))
        self.under20.setText(QCoreApplication.translate("SearchWidget", u"Under 20", None))
        self.under30.setText(QCoreApplication.translate("SearchWidget", u"Under 30", None))
        self.above.setText(QCoreApplication.translate("SearchWidget", u"14.99 and above", None))
        self.on_discount.setText(QCoreApplication.translate("SearchWidget", u"Discount", None))
        self.platform_group.setTitle(QCoreApplication.translate("SearchWidget", u"Platform", None))
        self.genre_group.setTitle(QCoreApplication.translate("SearchWidget", u"Genre", None))
        self.type_group.setTitle(QCoreApplication.translate("SearchWidget", u"Type", None))
        self.others_group.setTitle(QCoreApplication.translate("SearchWidget", u"Other tags", None))
        pass
    # retranslateUi


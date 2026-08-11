
################################################################################
## Form generated from reading UI file 'landing.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QRect, Qt
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QCheckBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class Ui_LandingWidget:
    def setupUi(self, LandingWidget):
        if not LandingWidget.objectName():
            LandingWidget.setObjectName("LandingWidget")
        LandingWidget.resize(788, 662)
        LandingWidget.setWindowTitle("LandingWidget")
        self.main_layout = QHBoxLayout(LandingWidget)
        self.main_layout.setObjectName("main_layout")
        self.left_layout = QVBoxLayout()
        self.left_layout.setObjectName("left_layout")

        self.main_layout.addLayout(self.left_layout)

        self.right_layout = QVBoxLayout()
        self.right_layout.setObjectName("right_layout")
        self.reset_button = QPushButton(LandingWidget)
        self.reset_button.setObjectName("reset_button")

        self.right_layout.addWidget(self.reset_button)

        self.filter_scrollarea = QScrollArea(LandingWidget)
        self.filter_scrollarea.setObjectName("filter_scrollarea")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.filter_scrollarea.sizePolicy().hasHeightForWidth())
        self.filter_scrollarea.setSizePolicy(sizePolicy)
        self.filter_scrollarea.setFrameShape(QFrame.NoFrame)
        self.filter_scrollarea.setFrameShadow(QFrame.Plain)
        self.filter_scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.filter_scrollarea.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.filter_scrollarea.setWidgetResizable(True)
        self.filter_container = QWidget()
        self.filter_container.setObjectName("filter_container")
        self.filter_container.setGeometry(QRect(0, 0, 142, 390))
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.filter_container.sizePolicy().hasHeightForWidth())
        self.filter_container.setSizePolicy(sizePolicy1)
        self.filter_container_layout = QVBoxLayout(self.filter_container)
        self.filter_container_layout.setObjectName("filter_container_layout")
        self.filter_container_layout.setContentsMargins(0, 0, 3, 0)
        self.price_group = QGroupBox(self.filter_container)
        self.price_group.setObjectName("price_group")
        self.price_layout = QVBoxLayout(self.price_group)
        self.price_layout.setObjectName("price_layout")
        self.none_price = QRadioButton(self.price_group)
        self.none_price.setObjectName("none_price")
        self.none_price.setChecked(True)

        self.price_layout.addWidget(self.none_price)

        self.free_button = QRadioButton(self.price_group)
        self.free_button.setObjectName("free_button")

        self.price_layout.addWidget(self.free_button)

        self.under10 = QRadioButton(self.price_group)
        self.under10.setObjectName("under10")

        self.price_layout.addWidget(self.under10)

        self.under20 = QRadioButton(self.price_group)
        self.under20.setObjectName("under20")

        self.price_layout.addWidget(self.under20)

        self.under30 = QRadioButton(self.price_group)
        self.under30.setObjectName("under30")

        self.price_layout.addWidget(self.under30)

        self.above = QRadioButton(self.price_group)
        self.above.setObjectName("above")

        self.price_layout.addWidget(self.above)

        self.on_discount = QCheckBox(self.price_group)
        self.on_discount.setObjectName("on_discount")

        self.price_layout.addWidget(self.on_discount)


        self.filter_container_layout.addWidget(self.price_group)

        self.platform_group = QGroupBox(self.filter_container)
        self.platform_group.setObjectName("platform_group")
        self.platfrom_layout = QVBoxLayout(self.platform_group)
        self.platfrom_layout.setObjectName("platfrom_layout")

        self.filter_container_layout.addWidget(self.platform_group)

        self.genre_group = QGroupBox(self.filter_container)
        self.genre_group.setObjectName("genre_group")
        self.genre_layout = QVBoxLayout(self.genre_group)
        self.genre_layout.setObjectName("genre_layout")

        self.filter_container_layout.addWidget(self.genre_group)

        self.type_group = QGroupBox(self.filter_container)
        self.type_group.setObjectName("type_group")
        self.type_layout = QVBoxLayout(self.type_group)
        self.type_layout.setObjectName("type_layout")

        self.filter_container_layout.addWidget(self.type_group)

        self.others_group = QGroupBox(self.filter_container)
        self.others_group.setObjectName("others_group")
        self.others_layout = QVBoxLayout(self.others_group)
        self.others_layout.setObjectName("others_layout")

        self.filter_container_layout.addWidget(self.others_group)

        self.filter_scrollarea.setWidget(self.filter_container)

        self.right_layout.addWidget(self.filter_scrollarea)


        self.main_layout.addLayout(self.right_layout)

        self.main_layout.setStretch(0, 1)

        self.retranslateUi(LandingWidget)
    # setupUi

    def retranslateUi(self, LandingWidget):
        self.reset_button.setText(QCoreApplication.translate("LandingWidget", "Reset filters", None))
        self.price_group.setTitle(QCoreApplication.translate("LandingWidget", "Price", None))
        self.none_price.setText(QCoreApplication.translate("LandingWidget", "None", None))
        self.free_button.setText(QCoreApplication.translate("LandingWidget", "Free", None))
        self.under10.setText(QCoreApplication.translate("LandingWidget", "Under 10", None))
        self.under20.setText(QCoreApplication.translate("LandingWidget", "Under 20", None))
        self.under30.setText(QCoreApplication.translate("LandingWidget", "Under 30", None))
        self.above.setText(QCoreApplication.translate("LandingWidget", "14.99 and above", None))
        self.on_discount.setText(QCoreApplication.translate("LandingWidget", "Discount", None))
        self.platform_group.setTitle(QCoreApplication.translate("LandingWidget", "Platform", None))
        self.genre_group.setTitle(QCoreApplication.translate("LandingWidget", "Genre", None))
        self.type_group.setTitle(QCoreApplication.translate("LandingWidget", "Type", None))
        self.others_group.setTitle(QCoreApplication.translate("LandingWidget", "Other tags", None))
    # retranslateUi



################################################################################
## Form generated from reading UI file 'wishlist_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget


class Ui_WishlistWidget:
    def setupUi(self, WishlistWidget):
        if not WishlistWidget.objectName():
            WishlistWidget.setObjectName("WishlistWidget")
        WishlistWidget.resize(202, 94)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(WishlistWidget.sizePolicy().hasHeightForWidth())
        WishlistWidget.setSizePolicy(sizePolicy)
        WishlistWidget.setWindowTitle("WishlistWIdget")
        self.main_layout = QHBoxLayout(WishlistWidget)
        self.main_layout.setObjectName("main_layout")
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.info_widget = QWidget(WishlistWidget)
        self.info_widget.setObjectName("info_widget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.info_widget.sizePolicy().hasHeightForWidth())
        self.info_widget.setSizePolicy(sizePolicy1)
        self.verticalLayout_2 = QVBoxLayout(self.info_widget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.title_label = QLabel(self.info_widget)
        self.title_label.setObjectName("title_label")
        font = QFont()
        font.setPointSize(16)
        self.title_label.setFont(font)
        self.title_label.setText("TextLabel")
        self.title_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.title_label)

        self.developer = QLabel(self.info_widget)
        self.developer.setObjectName("developer")
        font1 = QFont()
        font1.setPointSize(12)
        self.developer.setFont(font1)
        self.developer.setText("TextLabel")

        self.verticalLayout_2.addWidget(self.developer)

        self.price_layout = QHBoxLayout()
        self.price_layout.setObjectName("price_layout")
        self.discount_price = QLabel(self.info_widget)
        self.discount_price.setObjectName("discount_price")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.discount_price.sizePolicy().hasHeightForWidth())
        self.discount_price.setSizePolicy(sizePolicy2)
        self.discount_price.setText("TextLabel")

        self.price_layout.addWidget(self.discount_price)

        self.price = QLabel(self.info_widget)
        self.price.setObjectName("price")
        self.price.setText("TextLabel")

        self.price_layout.addWidget(self.price)


        self.verticalLayout_2.addLayout(self.price_layout)


        self.main_layout.addWidget(self.info_widget, 0, Qt.AlignTop)

        self.delete_button = QPushButton(WishlistWidget)
        self.delete_button.setObjectName("delete_button")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.delete_button.sizePolicy().hasHeightForWidth())
        self.delete_button.setSizePolicy(sizePolicy3)

        self.main_layout.addWidget(self.delete_button)


        self.retranslateUi(WishlistWidget)
    # setupUi

    def retranslateUi(self, WishlistWidget):
        self.delete_button.setText("")
    # retranslateUi


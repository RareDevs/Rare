# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'rare/ui/components/tabs/store/widgets/wishlist_widget.ui'
#
# Created by: PyQt5 UI code generator 5.15.10
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_WishlistWidget(object):
    def setupUi(self, WishlistWidget):
        WishlistWidget.setObjectName("WishlistWidget")
        WishlistWidget.resize(202, 94)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(WishlistWidget.sizePolicy().hasHeightForWidth())
        WishlistWidget.setSizePolicy(sizePolicy)
        WishlistWidget.setWindowTitle("WishlistWIdget")
        self.main_layout = QtWidgets.QHBoxLayout(WishlistWidget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setObjectName("main_layout")
        self.info_widget = QtWidgets.QWidget(WishlistWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.info_widget.sizePolicy().hasHeightForWidth())
        self.info_widget.setSizePolicy(sizePolicy)
        self.info_widget.setObjectName("info_widget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.info_widget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.title_label = QtWidgets.QLabel(self.info_widget)
        font = QtGui.QFont()
        font.setPointSize(16)
        self.title_label.setFont(font)
        self.title_label.setText("TextLabel")
        self.title_label.setWordWrap(True)
        self.title_label.setObjectName("title_label")
        self.verticalLayout_2.addWidget(self.title_label)
        self.developer = QtWidgets.QLabel(self.info_widget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.developer.setFont(font)
        self.developer.setText("TextLabel")
        self.developer.setObjectName("developer")
        self.verticalLayout_2.addWidget(self.developer)
        self.price_layout = QtWidgets.QHBoxLayout()
        self.price_layout.setObjectName("price_layout")
        self.discount_price = QtWidgets.QLabel(self.info_widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.discount_price.sizePolicy().hasHeightForWidth())
        self.discount_price.setSizePolicy(sizePolicy)
        self.discount_price.setText("TextLabel")
        self.discount_price.setObjectName("discount_price")
        self.price_layout.addWidget(self.discount_price)
        self.price = QtWidgets.QLabel(self.info_widget)
        self.price.setText("TextLabel")
        self.price.setObjectName("price")
        self.price_layout.addWidget(self.price)
        self.verticalLayout_2.addLayout(self.price_layout)
        self.main_layout.addWidget(self.info_widget, 0, QtCore.Qt.AlignTop)
        self.delete_button = QtWidgets.QPushButton(WishlistWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.delete_button.sizePolicy().hasHeightForWidth())
        self.delete_button.setSizePolicy(sizePolicy)
        self.delete_button.setText("")
        self.delete_button.setObjectName("delete_button")
        self.main_layout.addWidget(self.delete_button)

        self.retranslateUi(WishlistWidget)

    def retranslateUi(self, WishlistWidget):
        pass


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    WishlistWidget = QtWidgets.QWidget()
    ui = Ui_WishlistWidget()
    ui.setupUi(WishlistWidget)
    WishlistWidget.show()
    sys.exit(app.exec_())

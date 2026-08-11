
################################################################################
## Form generated from reading UI file 'wishlist.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QRect, Qt
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class Ui_Wishlist:
    def setupUi(self, Wishlist):
        if not Wishlist.objectName():
            Wishlist.setObjectName("Wishlist")
        Wishlist.resize(489, 165)
        Wishlist.setWindowTitle("Wishlist")
        self.main_layout = QVBoxLayout(Wishlist)
        self.main_layout.setObjectName("main_layout")
        self.tool_layout = QHBoxLayout()
        self.tool_layout.setObjectName("tool_layout")
        self.filter_combo = QComboBox(Wishlist)
        self.filter_combo.setObjectName("filter_combo")

        self.tool_layout.addWidget(self.filter_combo)

        self.order_combo = QComboBox(Wishlist)
        self.order_combo.setObjectName("order_combo")

        self.tool_layout.addWidget(self.order_combo)

        self.reverse_check = QCheckBox(Wishlist)
        self.reverse_check.setObjectName("reverse_check")

        self.tool_layout.addWidget(self.reverse_check)

        self.hspacer_left = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.tool_layout.addItem(self.hspacer_left)

        self.reload_button = QPushButton(Wishlist)
        self.reload_button.setObjectName("reload_button")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.reload_button.sizePolicy().hasHeightForWidth())
        self.reload_button.setSizePolicy(sizePolicy)

        self.tool_layout.addWidget(self.reload_button)


        self.main_layout.addLayout(self.tool_layout)

        self.scrollarea = QScrollArea(Wishlist)
        self.scrollarea.setObjectName("scrollarea")
        self.scrollarea.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.scrollarea.setWidgetResizable(True)
        self.container = QWidget()
        self.container.setObjectName("container")
        self.container.setGeometry(QRect(0, 0, 473, 115))
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setObjectName("container_layout")
        self.no_games_label = QLabel(self.container)
        self.no_games_label.setObjectName("no_games_label")

        self.container_layout.addWidget(self.no_games_label, 0, Qt.AlignTop)

        self.scrollarea.setWidget(self.container)

        self.main_layout.addWidget(self.scrollarea)


        self.retranslateUi(Wishlist)
    # setupUi

    def retranslateUi(self, Wishlist):
        self.reverse_check.setText(QCoreApplication.translate("Wishlist", "Reverse", None))
        self.reload_button.setText("")
        self.no_games_label.setText(QCoreApplication.translate("Wishlist", "No games matching your filter", None))
    # retranslateUi


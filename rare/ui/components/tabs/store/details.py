# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'details.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLayout, QPushButton, QSizePolicy,
    QTextBrowser, QVBoxLayout, QWidget)

class Ui_StoreDetailsWidget(object):
    def setupUi(self, StoreDetailsWidget):
        if not StoreDetailsWidget.objectName():
            StoreDetailsWidget.setObjectName(u"StoreDetailsWidget")
        StoreDetailsWidget.resize(630, 382)
        StoreDetailsWidget.setWindowTitle(u"StoreDetailsWidget")
        self.main_layout = QHBoxLayout(StoreDetailsWidget)
        self.main_layout.setObjectName(u"main_layout")
        self.left_layout = QVBoxLayout()
        self.left_layout.setObjectName(u"left_layout")
        self.back_button = QPushButton(StoreDetailsWidget)
        self.back_button.setObjectName(u"back_button")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.back_button.sizePolicy().hasHeightForWidth())
        self.back_button.setSizePolicy(sizePolicy)
        self.back_button.setText(u"")
        self.back_button.setIconSize(QSize(32, 32))
        self.back_button.setFlat(True)

        self.left_layout.addWidget(self.back_button)


        self.main_layout.addLayout(self.left_layout)

        self.right_layout = QVBoxLayout()
        self.right_layout.setObjectName(u"right_layout")
        self.details_layout = QFormLayout()
        self.details_layout.setObjectName(u"details_layout")
        self.details_layout.setSizeConstraint(QLayout.SetFixedSize)
        self.details_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.details_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.details_layout.setHorizontalSpacing(12)
        self.details_layout.setVerticalSpacing(12)
        self.details_layout.setContentsMargins(6, 6, 6, 6)
        self.title_label = QLabel(StoreDetailsWidget)
        self.title_label.setObjectName(u"title_label")
        font = QFont()
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.details_layout.setWidget(0, QFormLayout.LabelRole, self.title_label)

        self.title = QLabel(StoreDetailsWidget)
        self.title.setObjectName(u"title")
        self.title.setText(u"title")
        self.title.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.details_layout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.title)

        self.developer_label = QLabel(StoreDetailsWidget)
        self.developer_label.setObjectName(u"developer_label")
        self.developer_label.setFont(font)
        self.developer_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.details_layout.setWidget(1, QFormLayout.LabelRole, self.developer_label)

        self.developer = QLabel(StoreDetailsWidget)
        self.developer.setObjectName(u"developer")
        self.developer.setText(u"developer")
        self.developer.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.details_layout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.developer)

        self.publisher_label = QLabel(StoreDetailsWidget)
        self.publisher_label.setObjectName(u"publisher_label")
        self.publisher_label.setFont(font)
        self.publisher_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.details_layout.setWidget(2, QFormLayout.LabelRole, self.publisher_label)

        self.publisher = QLabel(StoreDetailsWidget)
        self.publisher.setObjectName(u"publisher")
        self.publisher.setText(u"publisher")
        self.publisher.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.details_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.publisher)

        self.status_label = QLabel(StoreDetailsWidget)
        self.status_label.setObjectName(u"status_label")
        self.status_label.setFont(font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.details_layout.setWidget(3, QFormLayout.LabelRole, self.status_label)

        self.status = QLabel(StoreDetailsWidget)
        self.status.setObjectName(u"status")

        self.details_layout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.status)

        self.price_label = QLabel(StoreDetailsWidget)
        self.price_label.setObjectName(u"price_label")
        self.price_label.setFont(font)
        self.price_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.details_layout.setWidget(4, QFormLayout.LabelRole, self.price_label)

        self.tags_label = QLabel(StoreDetailsWidget)
        self.tags_label.setObjectName(u"tags_label")
        self.tags_label.setFont(font)
        self.tags_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.details_layout.setWidget(5, QFormLayout.LabelRole, self.tags_label)

        self.tags = QLabel(StoreDetailsWidget)
        self.tags.setObjectName(u"tags")
        self.tags.setText(u"tags")

        self.details_layout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.tags)

        self.social_links_label = QLabel(StoreDetailsWidget)
        self.social_links_label.setObjectName(u"social_links_label")
        self.social_links_label.setFont(font)
        self.social_links_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.details_layout.setWidget(6, QFormLayout.LabelRole, self.social_links_label)

        self.actions_label = QLabel(StoreDetailsWidget)
        self.actions_label.setObjectName(u"actions_label")
        self.actions_label.setFont(font)
        self.actions_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.details_layout.setWidget(7, QFormLayout.LabelRole, self.actions_label)

        self.social_links = QWidget(StoreDetailsWidget)
        self.social_links.setObjectName(u"social_links")
        self.social_links_layout = QHBoxLayout(self.social_links)
        self.social_links_layout.setObjectName(u"social_links_layout")
        self.social_links_layout.setSizeConstraint(QLayout.SetFixedSize)
        self.social_links_layout.setContentsMargins(0, 0, 0, 0)

        self.details_layout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.social_links)

        self.actions = QWidget(StoreDetailsWidget)
        self.actions.setObjectName(u"actions")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.actions.sizePolicy().hasHeightForWidth())
        self.actions.setSizePolicy(sizePolicy1)
        self.actions.setMinimumSize(QSize(250, 0))
        self.actions_layout = QVBoxLayout(self.actions)
        self.actions_layout.setObjectName(u"actions_layout")
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.store_button = QPushButton(self.actions)
        self.store_button.setObjectName(u"store_button")

        self.actions_layout.addWidget(self.store_button)

        self.wishlist_button = QPushButton(self.actions)
        self.wishlist_button.setObjectName(u"wishlist_button")

        self.actions_layout.addWidget(self.wishlist_button)


        self.details_layout.setWidget(7, QFormLayout.ItemRole.FieldRole, self.actions)

        self.price = QWidget(StoreDetailsWidget)
        self.price.setObjectName(u"price")
        sizePolicy1.setHeightForWidth(self.price.sizePolicy().hasHeightForWidth())
        self.price.setSizePolicy(sizePolicy1)
        self.price_layout = QHBoxLayout(self.price)
        self.price_layout.setObjectName(u"price_layout")
        self.price_layout.setSizeConstraint(QLayout.SetFixedSize)
        self.price_layout.setContentsMargins(0, 0, 0, 0)
        self.original_price = QLabel(self.price)
        self.original_price.setObjectName(u"original_price")
        self.original_price.setText(u"orignal")
        self.original_price.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.price_layout.addWidget(self.original_price)

        self.discount_price = QLabel(self.price)
        self.discount_price.setObjectName(u"discount_price")
        self.discount_price.setText(u"discount")

        self.price_layout.addWidget(self.discount_price)


        self.details_layout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.price)


        self.right_layout.addLayout(self.details_layout)

        self.requirements_frame = QFrame(StoreDetailsWidget)
        self.requirements_frame.setObjectName(u"requirements_frame")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.requirements_frame.sizePolicy().hasHeightForWidth())
        self.requirements_frame.setSizePolicy(sizePolicy2)
        self.requirements_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.requirements_frame.setFrameShadow(QFrame.Sunken)
        self.requirements_layout = QHBoxLayout(self.requirements_frame)
        self.requirements_layout.setObjectName(u"requirements_layout")
        self.requirements_layout.setContentsMargins(0, 0, 0, 0)

        self.right_layout.addWidget(self.requirements_frame)

        self.description_label = QTextBrowser(StoreDetailsWidget)
        self.description_label.setObjectName(u"description_label")
        self.description_label.setOpenExternalLinks(True)

        self.right_layout.addWidget(self.description_label)


        self.main_layout.addLayout(self.right_layout)

        self.main_layout.setStretch(1, 1)

        self.retranslateUi(StoreDetailsWidget)
    # setupUi

    def retranslateUi(self, StoreDetailsWidget):
        self.title_label.setText(QCoreApplication.translate("StoreDetailsWidget", u"Title", None))
        self.developer_label.setText(QCoreApplication.translate("StoreDetailsWidget", u"Developer", None))
        self.publisher_label.setText(QCoreApplication.translate("StoreDetailsWidget", u"Publisher", None))
        self.status_label.setText(QCoreApplication.translate("StoreDetailsWidget", u"Status", None))
        self.status.setText(QCoreApplication.translate("StoreDetailsWidget", u"You already own this game", None))
        self.price_label.setText(QCoreApplication.translate("StoreDetailsWidget", u"Price", None))
        self.tags_label.setText(QCoreApplication.translate("StoreDetailsWidget", u"Tags", None))
        self.social_links_label.setText(QCoreApplication.translate("StoreDetailsWidget", u"Links", None))
        self.actions_label.setText(QCoreApplication.translate("StoreDetailsWidget", u"Actions", None))
        self.store_button.setText(QCoreApplication.translate("StoreDetailsWidget", u"Buy in Epic Games Store", None))
        self.wishlist_button.setText(QCoreApplication.translate("StoreDetailsWidget", u"Add to wishlist", None))
        pass
    # retranslateUi


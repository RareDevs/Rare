import logging
from typing import List, Dict

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QFont, QDesktopServices, QKeyEvent
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QGridLayout,
    QSizePolicy,
)

from rare.components.tabs.store.api.models.diesel import DieselProduct, DieselProductDetail, DieselSystemDetail
from rare.components.tabs.store.api.models.response import CatalogOfferModel
from rare.components.tabs.store.store_api import StoreAPI
from rare.models.image import ImageSize
from rare.ui.components.tabs.store.details import Ui_StoreDetailsWidget
from rare.utils.misc import qta_icon
from rare.widgets.elide_label import ElideLabel
from rare.widgets.side_tab import SideTabWidget, SideTabContents
from .image import LoadingImageWidget

logger = logging.getLogger("StoreDetails")


class StoreDetailsWidget(QWidget, SideTabContents):
    back_clicked: Signal = Signal()

    # TODO Design
    def __init__(self, installed: List, store_api: StoreAPI, parent=None):
        super(StoreDetailsWidget, self).__init__(parent=parent)
        self.implements_scrollarea = True

        self.ui = Ui_StoreDetailsWidget()
        self.ui.setupUi(self)
        self.ui.main_layout.setContentsMargins(0, 0, 3, 0)

        self.store_api = store_api
        self.installed = installed
        self.catalog_offer: CatalogOfferModel = None

        self.image = LoadingImageWidget(store_api.cached_manager, self)
        self.image.setFixedSize(ImageSize.DisplayTall)
        self.ui.left_layout.insertWidget(0, self.image, alignment=Qt.AlignmentFlag.AlignTop)
        self.ui.left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.ui.wishlist_button.clicked.connect(self.add_to_wishlist)
        self.ui.store_button.clicked.connect(self.button_clicked)
        self.ui.wishlist_button.setVisible(True)
        self.in_wishlist = False
        self.wishlist = []

        self.requirements_tabs = SideTabWidget(parent=self.ui.requirements_frame)
        self.requirements_tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.ui.requirements_layout.addWidget(self.requirements_tabs)

        self.ui.back_button.setIcon(qta_icon("fa.chevron-left"))
        self.ui.back_button.clicked.connect(self.back_clicked)

        self.setDisabled(False)

    def handle_wishlist_update(self, wishlist: List[CatalogOfferModel]):
        if wishlist and wishlist[0] == "error":
            return
        self.wishlist = [game.id for game in wishlist]
        if self.id_str in self.wishlist:
            self.in_wishlist = True
            self.ui.wishlist_button.setText(self.tr("Remove from Wishlist"))
        else:
            self.in_wishlist = False

    def update_game(self, offer: CatalogOfferModel):
        self.ui.title.setText(offer.title)
        self.title_str = offer.title
        self.id_str = offer.id
        self.store_api.get_wishlist(self.handle_wishlist_update)

        # lk: delete tabs in reverse order because indices are updated on deletion
        while self.requirements_tabs.count():
            self.requirements_tabs.widget(0).deleteLater()
            self.requirements_tabs.removeTab(0)
        self.requirements_tabs.clear()

        slug = offer.productSlug
        if not slug:
            for mapping in offer.offerMappings:
                if mapping["pageType"] == "productHome":
                    slug = mapping["pageSlug"]
                    break
            else:
                logger.error("Could not get page information")
                slug = ""
        if "/home" in slug:
            slug = slug.replace("/home", "")
        self.slug = slug

        if offer.namespace in self.installed:
            self.ui.store_button.setText(self.tr("Show Game on Epic Page"))
            self.ui.status.setVisible(True)
        else:
            self.ui.store_button.setText(self.tr("Buy Game in Epic Games Store"))
            self.ui.status.setVisible(False)

        self.ui.original_price.setText(self.tr("Loading"))
        # self.title.setText(self.tr("Loading"))
        # self.image.setPixmap(QPixmap())
        is_bundle = False
        for i in offer.categories:
            if "bundles" in i.get("path", ""):
                is_bundle = True

        # init API request
        if slug:
            self.store_api.get_game_config_cms(offer.productSlug, is_bundle, self.data_received)
        # else:
        #     self.data_received({})
        self.catalog_offer = offer

    def add_to_wishlist(self):
        if not self.in_wishlist:
            self.store_api.add_to_wishlist(
                self.catalog_offer.namespace,
                self.catalog_offer.id,
                lambda success: self.ui.wishlist_button.setText(self.tr("Remove from wishlist"))
                if success
                else self.ui.wishlist_button.setText("Something went wrong")
            )
        else:
            self.store_api.remove_from_wishlist(
                self.catalog_offer.namespace,
                self.catalog_offer.id,
                lambda success: self.ui.wishlist_button.setText(self.tr("Add to wishlist"))
                if success
                else self.ui.wishlist_button.setText("Something went wrong"),
            )

    def data_received(self, product: DieselProduct):
        try:
            if product.pages:
                product_data: DieselProductDetail = product.pages[0].data
            else:
                product_data: DieselProductDetail = product.data
        except Exception as e:
            raise e
            logger.error(str(e))

        self.ui.original_price.setFont(self.font())
        price = self.catalog_offer.price.totalPrice.fmtPrice["originalPrice"]
        discount_price = self.catalog_offer.price.totalPrice.fmtPrice["discountPrice"]
        if price == "0" or price == 0:
            self.ui.original_price.setText(self.tr("Free"))
        else:
            self.ui.original_price.setText(price)
        if price != discount_price:
            font = self.font()
            font.setStrikeOut(True)
            self.ui.original_price.setFont(font)
            self.ui.discount_price.setText(
                discount_price
                if discount_price != "0"
                else self.tr("Free")
            )
            self.ui.discount_price.setVisible(True)
        else:
            self.ui.discount_price.setVisible(False)

        requirements = product_data.requirements
        if requirements and requirements.systems:
            for system in requirements.systems:
                req_widget = RequirementsWidget(system, self.requirements_tabs)
                self.requirements_tabs.addTab(req_widget, system.systemType)
            self.ui.requirements_frame.setVisible(True)
        else:
            self.ui.requirements_frame.setVisible(False)

        key_images = self.catalog_offer.keyImages
        img_url = key_images.for_dimensions(self.image.size().width(), self.image.size().height())
        # FIXME: check why there was no tall image
        if img_url:
            self.image.fetchPixmap(img_url.url)

        # self.image_stack.setCurrentIndex(0)
        about = product_data.about
        self.ui.description_label.setMarkdown(about.desciption)
        self.ui.developer.setText(about.developerAttribution)
        # try:
        #     if isinstance(aboudeveloper, list):
        #         self.ui.dev.setText(", ".join(self.game.developer))
        #     else:
        #         self.ui.dev.setText(self.game.developer)
        # except KeyError:
        #     pass
        tags = product_data.unmapped["meta"].get("tags", [])
        self.ui.tags.setText(", ".join(tags))

        # clear Layout
        for b in self.ui.social_links.findChildren(SocialButton, options=Qt.FindChildOption.FindDirectChildrenOnly):
            self.ui.social_links_layout.removeWidget(b)
            b.deleteLater()

        links = product_data.socialLinks
        link_count = 0
        for name, url in links.items():
            if name == "_type":
                continue
            name = name.replace("link", "").lower()
            if name == "homepage":
                icn = qta_icon("mdi.web", "fa.search", scale_factor=1.5)
            else:
                try:
                    icn = qta_icon(f"mdi.{name}", f"fa.{name}", scale_factor=1.5)
                except Exception as e:
                    logger.error(str(e))
                    continue

            button = SocialButton(icn, url, parent=self.ui.social_links)
            self.ui.social_links_layout.addWidget(button)
            link_count += 1

        self.ui.social_links.setEnabled(bool(link_count))

        self.setEnabled(True)

    # def add_wishlist_items(self, wishlist: List[CatalogGameModel]):
    #     wishlist = wishlist["data"]["Wishlist"]["wishlistItems"]["elements"]
    #     for game in wishlist:
    #         self.wishlist.append(game["offer"]["title"])

    def button_clicked(self):
        QDesktopServices.openUrl(QUrl(f"https://www.epicgames.com/store/{self.store_api.language_code}/p/{self.slug}"))

    def keyPressEvent(self, a0: QKeyEvent):
        if a0.key() == Qt.Key.Key_Escape:
            self.back_clicked.emit()


class SocialButton(QPushButton):
    def __init__(self, icn, url, parent=None):
        super(SocialButton, self).__init__(icn, "", parent=parent)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.url = url
        self.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        self.setToolTip(url)


class RequirementsWidget(QWidget, SideTabContents):
    def __init__(self, system: DieselSystemDetail, parent=None):
        super().__init__(parent=parent)
        self.implements_scrollarea = True

        bold_font = self.font()
        bold_font.setBold(True)

        req_layout = QGridLayout(self)
        min_label = QLabel(self.tr("Minimum"), parent=self)
        min_label.setFont(bold_font)
        rec_label = QLabel(self.tr("Recommend"), parent=self)
        rec_label.setFont(bold_font)
        req_layout.addWidget(min_label, 0, 1)
        req_layout.addWidget(rec_label, 0, 2)
        req_layout.setColumnStretch(1, 2)
        req_layout.setColumnStretch(2, 2)
        for i, detail in enumerate(system.details):
            req_layout.addWidget(QLabel(detail.title, parent=self), i + 1, 0)
            min_label = ElideLabel(detail.minimum, parent=self)
            req_layout.addWidget(min_label, i + 1, 1)
            rec_label = ElideLabel(detail.recommended, parent=self)
            req_layout.addWidget(rec_label, i + 1, 2)
        req_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

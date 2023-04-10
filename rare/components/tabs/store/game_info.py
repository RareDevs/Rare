import logging
from pprint import pprint
from typing import List

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QFont, QDesktopServices, QFontMetrics
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QGridLayout,
    QSizePolicy,
)

from rare.components.tabs.store.api.models.response import CatalogOfferModel, DieselProduct, DieselProductDetail
from rare.shared import LegendaryCoreSingleton
from rare.shared.image_manager import ImageSize
from rare.ui.components.tabs.store.shop_game_info import Ui_ShopInfo
from rare.utils.misc import icon
from rare.widgets.side_tab import SideTabWidget, SideTabContents
from rare.widgets.elide_label import ElideLabel
from .api.debug import DebugDialog
from .image_widget import ShopImageWidget

logger = logging.getLogger("ShopInfo")


class ShopGameInfo(QWidget, SideTabContents):

    # TODO Design
    def __init__(self, installed_titles: list, api_core, parent=None):
        super(ShopGameInfo, self).__init__(parent=parent)
        self.ui = Ui_ShopInfo()
        self.ui.setupUi(self)
        # self.core = LegendaryCoreSingleton()
        self.api_core = api_core
        self.installed = installed_titles
        self.ui.open_store_button.clicked.connect(self.button_clicked)
        self.image = ShopImageWidget(api_core.cached_manager, self)
        self.image.setFixedSize(ImageSize.Normal)
        self.ui.left_layout.insertWidget(0, self.image, alignment=Qt.AlignTop)

        self.offer: CatalogOfferModel = None
        self.data: dict = {}

        self.ui.wishlist_button.clicked.connect(self.add_to_wishlist)
        self.ui.wishlist_button.setVisible(True)
        self.in_wishlist = False
        self.wishlist = []

        self.requirements_tabs: SideTabWidget = SideTabWidget(parent=self.ui.requirements_frame)
        self.requirements_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.ui.requirements_layout.addWidget(self.requirements_tabs)

        self.setDisabled(True)

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
        debug = DebugDialog(offer.__dict__, None)
        debug.exec()
        self.set_title.emit(offer.title)
        self.ui.title.setText(offer.title)
        self.title_str = offer.title
        self.id_str = offer.id
        self.api_core.get_wishlist(self.handle_wishlist_update)
        # lk: delete tabs in reverse order because indices are updated on deletion
        while self.requirements_tabs.count():
            self.requirements_tabs.widget(0).deleteLater()
            self.requirements_tabs.removeTab(0)
        self.requirements_tabs.clear()
        slug = offer.product_slug
        if not slug:
            for mapping in offer.offer_mappings:
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
            self.ui.open_store_button.setText(self.tr("Show Game on Epic Page"))
            self.ui.owned_label.setVisible(True)
        else:
            self.ui.open_store_button.setText(self.tr("Buy Game in Epic Games Store"))
            self.ui.owned_label.setVisible(False)

        self.ui.price.setText(self.tr("Loading"))
        # self.title.setText(self.tr("Loading"))
        # self.image.setPixmap(QPixmap())
        is_bundle = False
        for i in offer.categories:
            if "bundles" in i.get("path", ""):
                is_bundle = True

        # init API request
        if slug:
            self.api_core.get_game(offer.product_slug, is_bundle, self.data_received)
        # else:
        #     self.data_received({})
        self.offer = offer

    def add_to_wishlist(self):
        if not self.in_wishlist:
            self.api_core.add_to_wishlist(
                self.offer.namespace,
                self.offer.id,
                lambda success: self.ui.wishlist_button.setText(self.tr("Remove from wishlist"))
                if success
                else self.ui.wishlist_button.setText("Something went wrong")
            )
        else:
            self.api_core.remove_from_wishlist(
                self.offer.namespace,
                self.offer.id,
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
            self.price.setText("Error")
            self.requirements_tabs.setEnabled(False)
            for img in self.data.get("keyImages"):
                if img["type"] in [
                    "DieselStoreFrontWide",
                    "OfferImageTall",
                    "VaultClosed",
                    "ProductLogo",
                ]:
                    self.image.fetchPixmap(img["url"])
                    break
            self.price.setText("")
            self.discount_price.setText("")
            self.social_group.setEnabled(False)
            self.tags.setText("")
            self.dev.setText(self.data.get("seller", {}).get("name", ""))
            return
        # self.title.setText(self.game.title)

        self.ui.price.setFont(QFont())
        price = self.offer.price.total_price["fmtPrice"]["originalPrice"]
        discount_price = self.offer.price.total_price["fmtPrice"]["discountPrice"]
        if price == "0" or price == 0:
            self.ui.price.setText(self.tr("Free"))
        else:
            self.ui.price.setText(price)
        if price != discount_price:
            font = QFont()
            font.setStrikeOut(True)
            self.ui.price.setFont(font)
            self.ui.discount_price.setText(
                discount_price
                if discount_price != "0"
                else self.tr("Free")
            )
            self.ui.discount_price.setVisible(True)
        else:
            self.ui.discount_price.setVisible(False)

        bold_font = QFont()
        bold_font.setBold(True)

        fm = QFontMetrics(self.font())
        requirements = product_data.requirements
        if requirements and requirements.systems:
            for system in requirements.systems:
                req_widget = QWidget(self.requirements_tabs)
                req_layout = QGridLayout(req_widget)
                req_widget.layout().setAlignment(Qt.AlignTop)
                req_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                min_label = QLabel(self.tr("Minimum"), parent=req_widget)
                min_label.setFont(bold_font)
                rec_label = QLabel(self.tr("Recommend"), parent=req_widget)
                rec_label.setFont(bold_font)
                req_layout.addWidget(min_label, 0, 1)
                req_layout.addWidget(rec_label, 0, 2)
                req_layout.setColumnStretch(1, 2)
                req_layout.setColumnStretch(2, 2)
                for i, detail in enumerate(system.details):
                    req_layout.addWidget(QLabel(detail.title, parent=req_widget), i + 1, 0)
                    min_label = ElideLabel(detail.minimum, parent=req_widget)
                    req_layout.addWidget(min_label, i + 1, 1)
                    rec_label = ElideLabel(detail.recommended, parent=req_widget)
                    req_layout.addWidget(rec_label, i + 1, 2)
                self.requirements_tabs.addTab(req_widget, system.system_type)
                # self.req_group_box.layout().addWidget(req_tabs)
                # self.req_group_box.layout().setAlignment(Qt.AlignTop)
            # else:
            #     self.req_group_box.layout().addWidget(
            #         QLabel(self.tr("Could not get requirements"))
            #     )
            self.ui.requirements_frame.setVisible(True)
        else:
            self.ui.requirements_frame.setVisible(False)

        key_images = self.offer.key_images
        img_url = key_images.for_dimensions(self.image.size().width(), self.image.size().height())
        self.image.fetchPixmap(img_url.url)

        # self.image_stack.setCurrentIndex(0)
        about = product_data.about
        self.ui.description_label.setText(about.desciption)
        self.ui.dev.setText(about.developer_attribution)
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
        for b in self.ui.social_group.findChildren(SocialButton, options=Qt.FindDirectChildrenOnly):
            self.ui.social_layout.removeWidget(b)
            b.deleteLater()

        links = product_data.social_links
        link_count = 0
        for name, url in links.items():
            if name == "_type":
                continue
            name = name.replace("link", "").lower()
            if name == "homepage":
                icn = icon("mdi.web", "fa.search", scale_factor=1.5)
            else:
                try:
                    icn = icon(f"mdi.{name}", f"fa.{name}", scale_factor=1.5)
                except Exception as e:
                    logger.error(str(e))
                    continue

            button = SocialButton(icn, url, parent=self.ui.social_group)
            self.ui.social_layout.addWidget(button)
            link_count += 1

        self.ui.social_group.setEnabled(bool(link_count))

        self.setEnabled(True)

    # def add_wishlist_items(self, wishlist: List[CatalogGameModel]):
    #     wishlist = wishlist["data"]["Wishlist"]["wishlistItems"]["elements"]
    #     for game in wishlist:
    #         self.wishlist.append(game["offer"]["title"])

    def button_clicked(self):
        return
        QDesktopServices.openUrl(QUrl(f"https://www.epicgames.com/store/{self.core.language_code}/p/{self.slug}"))


class SocialButton(QPushButton):
    def __init__(self, icn, url, parent=None):
        super(SocialButton, self).__init__(icn, "", parent=parent)
        self.url = url
        self.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        self.setToolTip(url)

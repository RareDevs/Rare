import logging

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QFont, QDesktopServices
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QGridLayout,
    QSizePolicy,
)

from rare.components.tabs.store.shop_models import ShopGame
from rare.shared import LegendaryCoreSingleton
from rare.shared.image_manager import ImageSize
from rare.ui.components.tabs.store.shop_game_info import Ui_ShopGameInfo
from rare.utils.misc import icon
from rare.widgets.side_tab import SideTabWidget
from .image_widget import ShopImageWidget

logger = logging.getLogger("ShopInfo")


class ShopGameInfo(QWidget, Ui_ShopGameInfo):

    # TODO Design
    def __init__(self, installed_titles: list, api_core, parent=None):
        super(ShopGameInfo, self).__init__(parent=parent)
        self.setupUi(self)
        self.core = LegendaryCoreSingleton()
        self.api_core = api_core
        self.installed = installed_titles
        self.open_store_button.clicked.connect(self.button_clicked)
        self.image = ShopImageWidget(self)
        self.image.setFixedSize(ImageSize.Normal)
        self.image_info_layout.insertWidget(0, self.image)

        self.game: ShopGame = None
        self.data: dict = {}

        self.wishlist_button.clicked.connect(self.add_to_wishlist)
        self.in_wishlist = False
        self.wishlist = []

        self.requirements_tabs: SideTabWidget = SideTabWidget(parent=self.requirements_group)
        self.requirements_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.requirements_layout.addWidget(self.requirements_tabs)

        self.setDisabled(True)

    def handle_wishlist_update(self, data):
        if data and data[0] == "error":
            return
        self.wishlist = [i["offer"]["title"] for i in data]
        if self.title_str in self.wishlist:
            self.in_wishlist = True
            self.wishlist_button.setVisible(True)
            self.wishlist_button.setText(self.tr("Remove from Wishlist"))
        else:
            self.in_wishlist = False
            self.wishlist_button.setVisible(False)

    def update_game(self, data: dict):
        self.title.setText(data["title"])
        self.title_str = data["title"]
        self.id_str = data["id"]
        self.api_core.get_wishlist(self.handle_wishlist_update)
        # lk: delete tabs in inverse order because indices are updated on deletion
        while self.requirements_tabs.count():
            self.requirements_tabs.widget(0).deleteLater()
            self.requirements_tabs.removeTab(0)
        self.requirements_tabs.clear()
        slug = data["productSlug"]
        if not slug:
            for mapping in data["offerMappings"]:
                if mapping["pageType"] == "productHome":
                    slug = mapping["pageSlug"]
                    break
            else:
                logger.error("Could not get page information")
                slug = ""
        if "/home" in slug:
            slug = slug.replace("/home", "")
        self.slug = slug

        if data["namespace"] in self.installed:
            self.open_store_button.setText(self.tr("Show Game on Epic Page"))
            self.owned_label.setVisible(True)
        else:
            self.open_store_button.setText(self.tr("Buy Game in Epic Games Store"))
            self.owned_label.setVisible(False)

        self.price.setText(self.tr("Loading"))
        self.wishlist_button.setVisible(False)
        # self.title.setText(self.tr("Loading"))
        # self.image.setPixmap(QPixmap())
        self.data = data
        is_bundle = False
        for i in data["categories"]:
            if "bundles" in i.get("path", ""):
                is_bundle = True

        # init API request
        if slug:
            self.api_core.get_game(slug, is_bundle, self.data_received)
        # else:
        #     self.data_received({})

    def add_to_wishlist(self):
        if not self.in_wishlist:
            return
            # self.api_core.add_to_wishlist(self.game.namespace, self.game.offer_id,
            #                             lambda success: self.wishlist_button.setText(self.tr("Remove from wishlist"))
            #                              if success else self.wishlist_button.setText("Something goes wrong"))
        else:
            self.api_core.remove_from_wishlist(
                self.game.namespace,
                self.game.offer_id,
                lambda success: self.wishlist_button.setVisible(False)
                if success
                else self.wishlist_button.setText("Something goes wrong"),
            )

    def data_received(self, game):
        try:
            self.game = ShopGame.from_json(game, self.data)
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
                    self.image.fetchPixmap(img["url"], self.id_str, self.title_str)
                    break
            self.price.setText("")
            self.discount_price.setText("")
            self.social_group.setEnabled(False)
            self.tags.setText("")
            self.dev.setText(self.data.get("seller", {}).get("name", ""))
            return
        self.title.setText(self.game.title)

        self.price.setFont(QFont())
        if self.game.price == "0" or self.game.price == 0:
            self.price.setText(self.tr("Free"))
        else:
            self.price.setText(self.game.price)
        if self.game.price != self.game.discount_price:
            font = QFont()
            font.setStrikeOut(True)
            self.price.setFont(font)
            self.discount_price.setText(
                self.game.discount_price
                if self.game.discount_price != "0"
                else self.tr("Free")
            )
            self.discount_price.setVisible(True)
        else:
            self.discount_price.setVisible(False)

        bold_font = QFont()
        bold_font.setBold(True)

        if self.game.reqs:
            for system in self.game.reqs:
                req_widget = QWidget(self.requirements_tabs)
                req_layout = QGridLayout(req_widget)
                req_layout.setSizeConstraint(QGridLayout.SetFixedSize)
                req_widget.layout().setAlignment(Qt.AlignTop)
                req_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                min_label = QLabel(self.tr("Minimum"), parent=req_widget)
                min_label.setFont(bold_font)
                rec_label = QLabel(self.tr("Recommend"), parent=req_widget)
                rec_label.setFont(bold_font)
                req_layout.addWidget(min_label, 0, 1)
                req_layout.addWidget(rec_label, 0, 2)
                for i, (key, value) in enumerate(self.game.reqs.get(system, {}).items()):
                    req_layout.addWidget(QLabel(key, parent=req_widget), i + 1, 0)
                    min_label = QLabel(value[0], parent=req_widget)
                    min_label.setWordWrap(False)
                    req_layout.addWidget(min_label, i + 1, 1)
                    rec_label = QLabel(value[1], parent=req_widget)
                    rec_label.setWordWrap(False)
                    req_layout.addWidget(rec_label, i + 1, 2)
                self.requirements_tabs.addTab(req_widget, system)
            # self.req_group_box.layout().addWidget(req_tabs)
            # self.req_group_box.layout().setAlignment(Qt.AlignTop)
        # else:
        #     self.req_group_box.layout().addWidget(
        #         QLabel(self.tr("Could not get requirements"))
        #     )
            self.requirements_tabs.setEnabled(True)
        if self.game.image_urls.front_tall:
            img_url = self.game.image_urls.front_tall
        elif self.game.image_urls.offer_image_tall:
            img_url = self.game.image_urls.offer_image_tall
        elif self.game.image_urls.product_logo:
            img_url = self.game.image_urls.product_logo
        else:
            img_url = ""
        self.image.fetchPixmap(img_url, self.game.id, self.game.title)

        # self.image_stack.setCurrentIndex(0)
        try:
            if isinstance(self.game.developer, list):
                self.dev.setText(", ".join(self.game.developer))
            else:
                self.dev.setText(self.game.developer)
        except KeyError:
            pass
        self.tags.setText(", ".join(self.game.tags))

        # clear Layout
        for b in self.social_group.findChildren(SocialButton, options=Qt.FindDirectChildrenOnly):
            self.social_layout.removeWidget(b)
            b.deleteLater()

        link_count = 0
        for name, url in self.game.links:

            if name.lower() == "homepage":
                icn = icon("mdi.web", "fa.search", scale_factor=1.5)
            else:
                try:
                    icn = icon(f"mdi.{name.lower()}", f"fa.{name.lower()}", scale_factor=1.5)
                except Exception as e:
                    logger.error(str(e))
                    continue

            button = SocialButton(icn, url, parent=self.social_group)
            self.social_layout.addWidget(button)
            link_count += 1

        self.social_group.setEnabled(bool(link_count))

        self.setEnabled(True)

    def add_wishlist_items(self, wishlist):
        wishlist = wishlist["data"]["Wishlist"]["wishlistItems"]["elements"]
        for game in wishlist:
            self.wishlist.append(game["offer"]["title"])

    def button_clicked(self):
        QDesktopServices.openUrl(QUrl(f"https://www.epicgames.com/store/{self.core.language_code}/p/{self.slug}"))


class SocialButton(QPushButton):
    def __init__(self, icn, url, parent=None):
        super(SocialButton, self).__init__(icn, "", parent=parent)
        self.url = url
        self.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        self.setToolTip(url)

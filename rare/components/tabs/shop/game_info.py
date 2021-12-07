import logging
import webbrowser

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QSpacerItem, QGroupBox, QTabWidget, QGridLayout
from qtawesome import icon

from rare import shared
from rare.components.tabs.shop.shop_models import ShopGame
from rare.ui.components.tabs.store.shop_game_info import Ui_shop_info
from rare.utils.extra_widgets import WaitingSpinner, ImageLabel

logger = logging.getLogger("ShopInfo")


class ShopGameInfo(QWidget, Ui_shop_info):
    game: ShopGame
    data: dict

    # TODO Design
    def __init__(self, installed_titles: list, api_core):
        super(ShopGameInfo, self).__init__()
        self.setupUi(self)
        self.api_core = api_core
        self.installed = installed_titles
        self.open_store_button.clicked.connect(self.button_clicked)
        self.image = ImageLabel()
        self.image_stack.addWidget(self.image)
        self.image_stack.addWidget(WaitingSpinner())
        warn_label = QLabel()
        warn_label.setPixmap(icon("fa.warning").pixmap(160, 160).scaled(240, 320, Qt.IgnoreAspectRatio))
        self.image_stack.addWidget(warn_label)

        self.wishlist_button.clicked.connect(self.add_to_wishlist)
        self.in_wishlist = False
        self.wishlist = []

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
        self.image_stack.setCurrentIndex(1)
        self.title.setText(data["title"])
        self.title_str = data["title"]
        self.api_core.get_wishlist(self.handle_wishlist_update)
        for i in reversed(range(self.req_group_box.layout().count())):
            self.req_group_box.layout().itemAt(i).widget().deleteLater()
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

        for i in range(self.req_group_box.layout().count()):
            self.req_group_box.layout().itemAt(i).widget().deleteLater()

        self.price.setText(self.tr("Loading"))
        self.wishlist_button.setVisible(False)
        # self.title.setText(self.tr("Loading"))
        self.image.setPixmap(QPixmap())
        self.data = data
        is_bundle = False
        for i in data["categories"]:
            if "bundles" in i.get("path", ""):
                is_bundle = True

        # init API request
        if slug:
            self.api_core.get_game(slug, is_bundle, self.data_received)
        else:
            self.data_received({})

    def add_to_wishlist(self):
        if not self.in_wishlist:
            return
            # self.api_core.add_to_wishlist(self.game.namespace, self.game.offer_id,
            #                             lambda success: self.wishlist_button.setText(self.tr("Remove from wishlist"))
            #                              if success else self.wishlist_button.setText("Something goes wrong"))
        else:
            self.api_core.remove_from_wishlist(self.game.namespace, self.game.offer_id,
                                               lambda success: self.wishlist_button.setVisible(False)
                                               if success else self.wishlist_button.setText("Something goes wrong"))

    def data_received(self, game):
        try:
            self.game = ShopGame.from_json(game, self.data)
        except Exception as e:
            logger.error(str(e))
            self.price.setText("Error")
            self.req_group_box.setVisible(False)
            for img in self.data.get("keyImages"):
                if img["type"] in ["DieselStoreFrontWide", "OfferImageTall", "VaultClosed", "ProductLogo"]:
                    self.image.update_image(img["url"], size=(240, 320))
                    self.image_stack.setCurrentIndex(0)
                    break
            else:
                self.image_stack.setCurrentIndex(2)
            self.price.setText("")
            self.discount_price.setText("")
            self.social_link_gb.setVisible(False)
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
                self.game.discount_price if self.game.discount_price != "0" else self.tr("Free"))
            self.discount_price.setVisible(True)
        else:
            self.discount_price.setVisible(False)

        bold_font = QFont()
        bold_font.setBold(True)

        if self.game.reqs:
            req_tabs = QTabWidget()
            for system in self.game.reqs:
                min_label = QLabel(self.tr("Minimum"))
                min_label.setFont(bold_font)
                rec_label = QLabel(self.tr("Recommend"))
                rec_label.setFont(bold_font)
                req_widget = QWidget()
                req_widget.setLayout(QGridLayout())
                req_widget.layout().addWidget(min_label, 0, 1)
                req_widget.layout().addWidget(rec_label, 0, 2)
                for i, (key, value) in enumerate(self.game.reqs.get(system, {}).items()):
                    req_widget.layout().addWidget(QLabel(key), i + 1, 0)
                    min_label = QLabel(value[0])
                    min_label.setWordWrap(True)
                    req_widget.layout().addWidget(min_label, i + 1, 1)
                    rec_label = QLabel(value[1])
                    rec_label.setWordWrap(True)
                    req_widget.layout().addWidget(rec_label, i + 1, 2)
                req_tabs.addTab(req_widget, system)
            self.req_group_box.layout().addWidget(req_tabs)
        else:
            self.req_group_box.layout().addWidget(QLabel(self.tr("Could not get requirements")))
        self.req_group_box.setVisible(True)
        if self.game.image_urls.front_tall:
            img_url = self.game.image_urls.front_tall
        elif self.game.image_urls.offer_image_tall:
            img_url = self.game.image_urls.offer_image_tall
        elif self.game.image_urls.product_logo:
            img_url = self.game.image_urls.product_logo
        else:
            img_url = ""
        self.image.update_image(img_url, self.game.title, (240, 320))

        self.image_stack.setCurrentIndex(0)
        try:
            if isinstance(self.game.developer, list):
                self.dev.setText(", ".join(self.game.developer))
            else:
                self.dev.setText(self.game.developer)
        except KeyError:
            pass
        self.tags.setText(", ".join(self.game.tags))

        # clear Layout
        for widget in (self.social_link_gb.layout().itemAt(i) for i in range(self.social_link_gb.layout().count())):
            if not isinstance(widget, QSpacerItem):
                widget.widget().deleteLater()
        self.social_link_gb.deleteLater()
        self.social_link_gb = QGroupBox(self.tr("Social Links"))
        self.social_link_gb.setLayout(QHBoxLayout())

        self.layout().insertWidget(3, self.social_link_gb)

        self.social_link_gb.layout().addStretch(1)
        link_count = 0
        for name, url in self.game.links:

            if name.lower() == "homepage":
                icn = icon("mdi.web", scale_factor=1.5)
            else:
                try:
                    icn = icon("mdi." + name.lower(), scale_factor=1.5)
                except Exception as e:
                    logger.error(str(e))
                    continue

            button = SocialButton(icn, url)
            self.social_link_gb.layout().addWidget(button)
            link_count += 1
            self.social_link_gb.layout().addStretch(1)

        if link_count == 0:
            self.social_link_gb.setVisible(False)
        else:
            self.social_link_gb.setVisible(True)
        self.social_link_gb.layout().addStretch(1)

    def add_wishlist_items(self, wishlist):
        wishlist = wishlist["data"]["Wishlist"]["wishlistItems"]["elements"]
        for game in wishlist:
            self.wishlist.append(game["offer"]["title"])

    def button_clicked(self):
        webbrowser.open(f"https://www.epicgames.com/store/{shared.core.language_code}/p/" + self.slug)


class SocialButton(QPushButton):
    def __init__(self, icn, url):
        super(SocialButton, self).__init__(icn, "")
        self.url = url
        self.clicked.connect(lambda: webbrowser.open(url))
        self.setToolTip(url)

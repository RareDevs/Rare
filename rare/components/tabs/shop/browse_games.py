import datetime
import json
import logging
import random

from PyQt5.QtCore import QUrl, pyqtSignal, QJsonParseError, QJsonDocument
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkAccessManager
from PyQt5.QtWidgets import QWidget

from rare.components.tabs.shop.game_widgets import GameWidget
from rare.ui.components.tabs.store.browse_games import Ui_browse_games
from rare.utils.extra_widgets import FlowLayout, WaitingSpinner
from rare.utils.utils import get_lang

logger = logging.getLogger("BrowseGames")


class BrowseGames(QWidget, Ui_browse_games):
    show_game = pyqtSignal(dict)
    price = ""
    platform = (False, False)

    def __init__(self, path):
        super(BrowseGames, self).__init__()
        self.setupUi(self)
        self.path = path
        self.games_widget = QWidget()
        self.games_widget.setLayout(FlowLayout())
        self.games.setWidget(self.games_widget)
        self.manager = QNetworkAccessManager()

        self.stack.addWidget(WaitingSpinner())

        self.clear_price.toggled.connect(lambda: self.prepare_request("") if self.clear_price.isChecked() else None)
        self.free_button.toggled.connect(lambda: self.prepare_request("free") if self.free_button.isChecked() else None)
        self.under10.toggled.connect(
            lambda: self.prepare_request("<price>[0, 1000)") if self.under10.isChecked() else None)
        self.under20.toggled.connect(
            lambda: self.prepare_request("<price>[0, 2000)") if self.under20.isChecked() else None)
        self.under30.toggled.connect(
            lambda: self.prepare_request("<price>[0, 3000)") if self.under30.isChecked() else None)
        self.above.toggled.connect(lambda: self.prepare_request("<price>[1499,]") if self.above.isChecked() else None)
        self.on_discount.toggled.connect(lambda: self.prepare_request("sale") if self.on_discount.isChecked() else None)

        self.win_cb.toggled.connect(
            lambda: self.prepare_request(platform=(self.win_cb.isChecked(), self.mac_cb.isChecked())))
        self.mac_cb.toggled.connect(
            lambda: self.prepare_request(platform=(self.win_cb.isChecked(), self.mac_cb.isChecked())))

    def prepare_request(self, price: str = None, platform: tuple = None):
        if price is not None:
            self.price = price
        if platform is not None:
            self.platform = platform

        locale = get_lang()
        self.stack.setCurrentIndex(2)
        date = f"[,{datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%dT%X')}.{str(random.randint(0, 999)).zfill(3)}Z]"
        payload = {"variables": {"category": "games/edition/base|bundles/games|editors|software/edition/base",
                                 "count": 30, "country": locale.upper(), "keywords": "", "locale": locale,
                                 "sortDir": "DESC", "allowCountries": locale.upper(), "start": 0, "tag": "",
                                 "withMapping": True, "withPrice": True,
                                 "releaseDate": date, "effectiveDate": date
                                 },
                   "query": game_query}

        if self.price == "free":
            payload["variables"]["freeGame"] = True
        elif self.price.startswith("<price>"):
            payload["variables"]["priceRange"] = price.replace("<price>", "")
        elif self.price == "sale":
            payload["variables"]["onSale"] = True

        if self.platform[0]:
            payload["variables"]["tag"] = "9547"
            if self.platform[1]:
                payload["variables"]["tag"] += "|10719"
        elif self.platform[1]:
            payload["variables"]["tag"] = "10719"

        request = QNetworkRequest(QUrl("https://www.epicgames.com/graphql"))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        self.game_request = self.manager.post(request, json.dumps(payload).encode("utf-8"))
        self.game_request.finished.connect(self.show_games)

    def show_games(self):
        if self.game_request:
            if self.game_request.error() == QNetworkReply.NoError:
                error = QJsonParseError()
                json_data = QJsonDocument.fromJson(self.game_request.readAll().data(), error)

                if error.error == error.NoError:
                    try:
                        games = json.loads(json_data.toJson().data().decode())["data"]["Catalog"]["searchStore"][
                            "elements"]
                    except TypeError as e:
                        logger.error("Type Error: " + str(e))
                        self.stack.setCurrentIndex(1)
                    else:
                        QWidget().setLayout(self.games_widget.layout())
                        self.games_widget.setLayout(FlowLayout())

                        for game in games:
                            w = GameWidget(self.path, game, 275)
                            self.games_widget.layout().addWidget(w)
                            w.show_info.connect(self.show_game.emit)
                        self.stack.setCurrentIndex(0)
                        return

                else:
                    logger.info(self.slug, error.errorString())
            else:
                print(self.game_request.errorString())
        self.stack.setCurrentIndex(1)


game_query = "query searchStoreQuery($allowCountries: String, $category: String, $count: Int, $country: String!, " \
             "$keywords: String, $locale: String, $namespace: String, $withMapping: Boolean = false, $itemNs: String, " \
             "$sortBy: String, $sortDir: String, $start: Int, $tag: String, $releaseDate: String, $withPrice: Boolean " \
             "= false, $withPromotions: Boolean = false, $priceRange: String, $freeGame: Boolean, $onSale: Boolean, " \
             "$effectiveDate: String) {\n  Catalog {\n    searchStore(\n      allowCountries: $allowCountries\n      " \
             "category: $category\n      count: $count\n      country: $country\n      keywords: $keywords\n      " \
             "locale: $locale\n      namespace: $namespace\n      itemNs: $itemNs\n      sortBy: $sortBy\n      " \
             "sortDir: $sortDir\n      releaseDate: $releaseDate\n      start: $start\n      tag: $tag\n      " \
             "priceRange: $priceRange\n      freeGame: $freeGame\n      onSale: $onSale\n      effectiveDate: " \
             "$effectiveDate\n    ) {\n      elements {\n        title\n        id\n        namespace\n        " \
             "description\n        effectiveDate\n        keyImages {\n          type\n          url\n        }\n     " \
             "   currentPrice\n        seller {\n          id\n          name\n        }\n        productSlug\n       " \
             " urlSlug\n        url\n        tags {\n          id\n        }\n        items {\n          id\n         " \
             " namespace\n        }\n        customAttributes {\n          key\n          value\n        }\n        " \
             "categories {\n          path\n        }\n        catalogNs @include(if: $withMapping) {\n          " \
             "mappings(pageType: \"productHome\") {\n            pageSlug\n            pageType\n          }\n        " \
             "}\n        offerMappings @include(if: $withMapping) {\n          pageSlug\n          pageType\n        " \
             "}\n        price(country: $country) @include(if: $withPrice) {\n          totalPrice {\n            " \
             "discountPrice\n            originalPrice\n            voucherDiscount\n            discount\n           " \
             " currencyCode\n            currencyInfo {\n              decimals\n            }\n            fmtPrice(" \
             "locale: $locale) {\n              originalPrice\n              discountPrice\n              " \
             "intermediatePrice\n            }\n          }\n          lineOffers {\n            appliedRules {\n     " \
             "         id\n              endDate\n              discountSetting {\n                discountType\n     " \
             "         }\n            }\n          }\n        }\n        promotions(category: $category) @include(if: " \
             "$withPromotions) {\n          promotionalOffers {\n            promotionalOffers {\n              " \
             "startDate\n              endDate\n              discountSetting {\n                discountType\n       " \
             "         discountPercentage\n              }\n            }\n          }\n          " \
             "upcomingPromotionalOffers {\n            promotionalOffers {\n              startDate\n              " \
             "endDate\n              discountSetting {\n                discountType\n                " \
             "discountPercentage\n              }\n            }\n          }\n        }\n      }\n      paging {\n   " \
             "     count\n        total\n      }\n    }\n  }\n}\n "

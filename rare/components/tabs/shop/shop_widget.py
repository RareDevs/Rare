import datetime
import json
import logging
import os
from json import JSONDecodeError

import requests
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QByteArray, QJsonDocument, QJsonParseError, \
    QStringListModel
from PyQt5.QtGui import QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QCompleter

from rare.ui.components.tabs.store.store import Ui_ShopWidget
from rare.utils.extra_widgets import WaitingSpinner, ImageLabel
from rare.utils.utils import get_lang


class ShopWidget(QWidget, Ui_ShopWidget):
    show_info = pyqtSignal(list)
    show_game = pyqtSignal(dict)
    free_game_widgets = []

    def __init__(self):
        super(ShopWidget, self).__init__()
        self.setupUi(self)
        self.search_results.setVisible(False)
        self.manager = QNetworkAccessManager()
        self.free_games_stack.addWidget(WaitingSpinner())
        self.free_games_stack.setCurrentIndex(1)
        self.search.textChanged.connect(self.search_games)
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search.setCompleter(self.completer)
        self.search.returnPressed.connect(self.show_search_result)
        self.data = []

    def load(self):
        if p := os.getenv("XDG_CACHE_HOME"):
            self.path = p
        else:
            self.path = os.path.expanduser("~/.cache/rare/cache/")
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
        self.free_game_request = self.manager.get(QNetworkRequest(QUrl(url)))
        self.free_game_request.readyRead.connect(self.add_free_games)
        self.free_game_request.finished.connect(self.free_game_request.deleteLater if self.free_game_request else None)

        # free_games = api_utils.get_free_games()

    def add_free_games(self):
        if self.free_game_request:
            if self.free_game_request.error() == QNetworkReply.NoError:
                try:
                    free_games = json.loads(self.free_game_request.readAll().data().decode())
                except JSONDecodeError:
                    return
            else:
                return
        else:
            return
        free_games = free_games["data"]["Catalog"]["searchStore"]["elements"]
        date = datetime.datetime.now()
        free_games_now = []
        coming_free_games = []
        for game in free_games:
            if game["title"] == "Mystery Game":
                coming_free_games.append(game)
                continue
            try:
                # parse datetime
                end_date = datetime.datetime.strptime(
                    game["promotions"].get("promotionalOffers", game["promotions"].get("upcomingPromotionalOffers"))[0][
                        "promotionalOffers"][0]["endDate"],
                    '%Y-%m-%dT%H:%M:%S.%fZ')
                start_date = datetime.datetime.strptime(
                    game["promotions"].get("promotionalOffers", game["promotions"].get("upcomingPromotionalOffers"))[0][
                        "promotionalOffers"][0]["startDate"],
                    '%Y-%m-%dT%H:%M:%S.%fZ')
            except IndexError:
                print("index error")
                continue
            except KeyError:
                print("keyerror")
                continue
            except TypeError:
                print("type error")
                continue
            if start_date < date < end_date:
                free_games_now.append(game)
            elif start_date > date:
                coming_free_games.append(game)

        for free_game in free_games_now:
            w = GameWidget(free_game, self.path)
            w.show_info.connect(lambda x: self.search_games(x, True))
            self.free_game_now.layout().addWidget(w)
            self.free_game_widgets.append(w)
            self.free_game_group_box_2.setMinimumHeight(200)

        for free_game in coming_free_games:
            w = GameWidget(free_game, self.path)
            if free_game["title"] != "Mystery Game":
                w.show_info.connect(self.show_info)
            self.comming_free_game.layout().addWidget(w)
            self.free_game_widgets.append(w)
        self.free_games_stack.setCurrentIndex(0)

    def search_games(self, text, show_direct=False):
        if text == "":
            self.search_results.setVisible(False)
        else:
            locale = get_lang()
            payload = QByteArray()
            payload.append(
                "query=query searchStoreQuery($allowCountries: String, $category: String, $count: Int, $country: String!, $keywords: String, $locale: String, $namespace: String, $withMapping: Boolean = false, $itemNs: String, $sortBy: String, $sortDir: String, $start: Int, $tag: String, $releaseDate: String, $withPrice: Boolean = false, $withPromotions: Boolean = false, $priceRange: String, $freeGame: Boolean, $onSale: Boolean, $effectiveDate: String) {\n  Catalog {\n    searchStore(\n      allowCountries: $allowCountries\n      category: $category\n      count: $count\n      country: $country\n      keywords: $keywords\n      locale: $locale\n      namespace: $namespace\n      itemNs: $itemNs\n      sortBy: $sortBy\n      sortDir: $sortDir\n      releaseDate: $releaseDate\n      start: $start\n      tag: $tag\n      priceRange: $priceRange\n      freeGame: $freeGame\n      onSale: $onSale\n      effectiveDate: $effectiveDate\n    ) {\n      elements {\n        title\n        id\n        namespace\n        description\n        effectiveDate\n        keyImages {\n          type\n          url\n        }\n        currentPrice\n        seller {\n          id\n          name\n        }\n        productSlug\n        urlSlug\n        url\n        tags {\n          id\n        }\n        items {\n          id\n          namespace\n        }\n        customAttributes {\n          key\n          value\n        }\n        categories {\n          path\n        }\n        catalogNs @include(if: $withMapping) {\n          mappings(pageType: \"productHome\") {\n            pageSlug\n            pageType\n          }\n        }\n        offerMappings @include(if: $withMapping) {\n          pageSlug\n          pageType\n        }\n        price(country: $country) @include(if: $withPrice) {\n          totalPrice {\n            discountPrice\n            originalPrice\n            voucherDiscount\n            discount\n            currencyCode\n            currencyInfo {\n              decimals\n            }\n            fmtPrice(locale: $locale) {\n              originalPrice\n              discountPrice\n              intermediatePrice\n            }\n          }\n          lineOffers {\n            appliedRules {\n              id\n              endDate\n              discountSetting {\n                discountType\n              }\n            }\n          }\n        }\n        promotions(category: $category) @include(if: $withPromotions) {\n          promotionalOffers {\n            promotionalOffers {\n              startDate\n              endDate\n              discountSetting {\n                discountType\n                discountPercentage\n              }\n            }\n          }\n          upcomingPromotionalOffers {\n            promotionalOffers {\n              startDate\n              endDate\n              discountSetting {\n                discountType\n                discountPercentage\n              }\n            }\n          }\n        }\n      }\n      paging {\n        count\n        total\n      }\n    }\n  }\n}\n")

            payload = json.dumps({
                "query": "query searchStoreQuery($allowCountries: String, $category: String, $count: Int, $country: String!, $keywords: String, $locale: String, $namespace: String, $withMapping: Boolean = false, $itemNs: String, $sortBy: String, $sortDir: String, $start: Int, $tag: String, $releaseDate: String, $withPrice: Boolean = false, $withPromotions: Boolean = false, $priceRange: String, $freeGame: Boolean, $onSale: Boolean, $effectiveDate: String) {\n  Catalog {\n    searchStore(\n      allowCountries: $allowCountries\n      category: $category\n      count: $count\n      country: $country\n      keywords: $keywords\n      locale: $locale\n      namespace: $namespace\n      itemNs: $itemNs\n      sortBy: $sortBy\n      sortDir: $sortDir\n      releaseDate: $releaseDate\n      start: $start\n      tag: $tag\n      priceRange: $priceRange\n      freeGame: $freeGame\n      onSale: $onSale\n      effectiveDate: $effectiveDate\n    ) {\n      elements {\n        title\n        id\n        namespace\n        description\n        effectiveDate\n        keyImages {\n          type\n          url\n        }\n        currentPrice\n        seller {\n          id\n          name\n        }\n        productSlug\n        urlSlug\n        url\n        tags {\n          id\n        }\n        items {\n          id\n          namespace\n        }\n        customAttributes {\n          key\n          value\n        }\n        categories {\n          path\n        }\n        catalogNs @include(if: $withMapping) {\n          mappings(pageType: \"productHome\") {\n            pageSlug\n            pageType\n          }\n        }\n        offerMappings @include(if: $withMapping) {\n          pageSlug\n          pageType\n        }\n        price(country: $country) @include(if: $withPrice) {\n          totalPrice {\n            discountPrice\n            originalPrice\n            voucherDiscount\n            discount\n            currencyCode\n            currencyInfo {\n              decimals\n            }\n            fmtPrice(locale: $locale) {\n              originalPrice\n              discountPrice\n              intermediatePrice\n            }\n          }\n          lineOffers {\n            appliedRules {\n              id\n              endDate\n              discountSetting {\n                discountType\n              }\n            }\n          }\n        }\n        promotions(category: $category) @include(if: $withPromotions) {\n          promotionalOffers {\n            promotionalOffers {\n              startDate\n              endDate\n              discountSetting {\n                discountType\n                discountPercentage\n              }\n            }\n          }\n          upcomingPromotionalOffers {\n            promotionalOffers {\n              startDate\n              endDate\n              discountSetting {\n                discountType\n                discountPercentage\n              }\n            }\n          }\n        }\n      }\n      paging {\n        count\n        total\n      }\n    }\n  }\n}\n",
                "variables": {"category": "games/edition/base|bundles/games|editors|software/edition/base", "count": 10,
                              "country": "DE", "keywords": text, "locale": locale, "sortDir": "DESC",
                              "allowCountries": locale.upper(),
                              "start": 0, "tag": "", "withMapping": False, "withPrice": True}
            }).encode()
            request = QNetworkRequest(QUrl("https://www.epicgames.com/graphql"))
            request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
            self.search_request = self.manager.post(request, payload)
            # self.search_request = self.manager.post(QNetworkRequest(QUrl("https://www.epicgames.com/graphql")), payload)
            self.search_request.finished.connect(lambda: self.show_search_results(show_direct))

    def show_search_results(self, show_direct=False):
        if self.search_request:
            if self.search_request.error() == QNetworkReply.NoError:
                error = QJsonParseError()
                json_data = QJsonDocument.fromJson(self.search_request.readAll().data(), error)
                if QJsonParseError.NoError == error.error:
                    data = json.loads(json_data.toJson().data().decode())["data"]["Catalog"]["searchStore"]["elements"]
                else:
                    logging.error(error.errorString())
                    self.search_results.setVisible(False)
                    return
                # response = .decode(encoding="utf-8")
                # print(response)
                # results = json.loads(response)
            else:
                return
        else:
            return
        self.data = data
        if show_direct:
            self.show_search_result(True)
            return
        titles = [i.get("title") for i in data]
        model = QStringListModel()
        model.setStringList(titles)
        self.completer.setModel(model)
        # self.completer.popup()
        # self.search_results.setLayout(layout)
        # self.search_results.setVisible(True)
        if self.search_request:
            self.search_request.deleteLater()

    def show_search_result(self, show_direct=False):
        if not show_direct:
            if self.data:
                self.show_info.emit(self.data)
        else:
            self.show_game.emit(self.data[0])


class GameWidget(QWidget):
    show_info = pyqtSignal(str)

    def __init__(self, json_info, path: str):
        super(GameWidget, self).__init__()
        self.layout = QVBoxLayout()
        self.image = ImageLabel()
        for img in json_info["keyImages"]:
            if img["type"] in ["DieselStoreFrontWide", "VaultClosed"]:
                width = 300
                self.image.update_image(img["url"], json_info["title"], (width, int(width * 9 / 16)))
                break
        else:
            print("No image found")

        self.slug = json_info["productSlug"]
        self.title = json_info["title"]
        if not os.path.exists(p := os.path.join(path, f"{json_info['title']}.png")):
            for img in json_info["keyImages"]:
                if json_info["title"] != "Mystery Game":
                    if img["type"] == "DieselStoreFrontWide":
                        with open(p, "wb") as img_file:
                            content = requests.get(img["url"]).content
                            img_file.write(content)
                            break
                else:
                    if img["type"] == "VaultClosed":
                        with open(p, "wb") as img_file:
                            content = requests.get(img["url"]).content
                            img_file.write(content)
                            break
            else:
                print("No image found")
        width = 300
        self.image.setPixmap(QPixmap(os.path.join(path, f"{json_info['title']}.png"))
                             .scaled(width, int(width * 9 / 16), transformMode=Qt.SmoothTransformation))
        self.layout.addWidget(self.image)

        self.title_label = QLabel(json_info["title"])
        self.layout.addWidget(self.title_label)
        self.setLayout(self.layout)

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.show_info.emit(self.title)

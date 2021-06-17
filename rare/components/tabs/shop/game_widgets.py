import json
import json
import logging

from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal, QUrl, QJsonParseError, QJsonDocument
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

from rare.utils.extra_widgets import ImageLabel
from rare.utils.utils import get_lang

logger = logging.getLogger("GameWidgets")


class GameWidget(QWidget):
    show_info = pyqtSignal(dict)

    def __init__(self, path, json_info=None, width=300):
        super(GameWidget, self).__init__()
        self.manager = QNetworkAccessManager()
        self.width = width
        if json_info:
            self.init_ui(json_info, path)
        self.path = path

    def init_ui(self, json_info, path):
        self.path = path
        self.layout = QVBoxLayout()
        self.image = ImageLabel()
        self.layout.addWidget(self.image)

        self.title_label = QLabel(json_info["title"])
        self.title_label.setWordWrap(True)
        self.layout.addWidget(self.title_label)

        for c in r'<>?":|\/*':
            json_info["title"] = json_info["title"].replace(c, "")

        self.json_info = json_info
        self.slug = json_info["productSlug"]

        self.title = json_info["title"]
        for img in json_info["keyImages"]:
            if img["type"] in ["DieselStoreFrontWide", "OfferImageWide", "VaultClosed"]:
                if img["type"] == "VaultClosed" and self.title != "Mystery Game":
                    continue
                self.image.update_image(img["url"], json_info["title"], (self.width, int(self.width * 9 / 16)))
                break
        else:
            logger.info(", ".join([img["type"] for img in json_info["keyImages"]]))
            # print(json_info["keyImages"])

        self.setLayout(self.layout)

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.show_info.emit(self.json_info)

    @classmethod
    def from_request(cls, name, path):
        c = cls(path)
        c.manager = QNetworkAccessManager()
        c.request = c.manager.get(QNetworkRequest())

        locale = get_lang()
        payload = json.dumps({
            "query": query,
            "variables": {"category": "games/edition/base|bundles/games|editors|software/edition/base", "count": 1,
                          "country": "DE", "keywords": name, "locale": locale, "sortDir": "DESC",
                          "allowCountries": locale.upper(),
                          "start": 0, "tag": "", "withMapping": False, "withPrice": True}
        }).encode()
        request = QNetworkRequest(QUrl("https://www.epicgames.com/graphql"))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        c.search_request = c.manager.post(request, payload)
        c.search_request.finished.connect(lambda: c.handle_response(path))
        return c

    def handle_response(self, path):
        if self.search_request:
            if self.search_request.error() == QNetworkReply.NoError:
                error = QJsonParseError()
                json_data = QJsonDocument.fromJson(self.search_request.readAll().data(), error)
                if QJsonParseError.NoError == error.error:
                    data = json.loads(json_data.toJson().data().decode())["data"]["Catalog"]["searchStore"][
                        "elements"][0]
                    self.init_ui(data, path)
                else:
                    logging.error(error.errorString())
                    return

            else:
                return
        else:
            return


query = "query searchStoreQuery($allowCountries: String, $category: String, $count: Int, $country: String!, " \
        "$keywords: String, $locale: String, $namespace: String, $withMapping: Boolean = false, $itemNs: String, " \
        "$sortBy: String, $sortDir: String, $start: Int, $tag: String, $releaseDate: String, $withPrice: Boolean = " \
        "false, $withPromotions: Boolean = false, $priceRange: String, $freeGame: Boolean, $onSale: Boolean, " \
        "$effectiveDate: String) {\n  Catalog {\n    searchStore(\n      allowCountries: $allowCountries\n      " \
        "category: $category\n      count: $count\n      country: $country\n      keywords: $keywords\n      locale: " \
        "$locale\n      namespace: $namespace\n      itemNs: $itemNs\n      sortBy: $sortBy\n      sortDir: " \
        "$sortDir\n      releaseDate: $releaseDate\n      start: $start\n      tag: $tag\n      priceRange: " \
        "$priceRange\n      freeGame: $freeGame\n      onSale: $onSale\n      effectiveDate: $effectiveDate\n    ) {" \
        "\n      elements {\n        title\n        id\n        namespace\n        description\n        " \
        "effectiveDate\n        keyImages {\n          type\n          url\n        }\n        currentPrice\n        " \
        "seller {\n          id\n          name\n        }\n        productSlug\n        urlSlug\n        url\n       " \
        " tags {\n          id\n        }\n        items {\n          id\n          namespace\n        }\n        " \
        "customAttributes {\n          key\n          value\n        }\n        categories {\n          path\n        " \
        "}\n        catalogNs @include(if: $withMapping) {\n          mappings(pageType: \"productHome\") {\n         " \
        "   pageSlug\n            pageType\n          }\n        }\n        offerMappings @include(if: $withMapping) " \
        "{\n          pageSlug\n          pageType\n        }\n        price(country: $country) @include(if: " \
        "$withPrice) {\n          totalPrice {\n            discountPrice\n            originalPrice\n            " \
        "voucherDiscount\n            discount\n            currencyCode\n            currencyInfo {\n              " \
        "decimals\n            }\n            fmtPrice(locale: $locale) {\n              originalPrice\n              " \
        "discountPrice\n              intermediatePrice\n            }\n          }\n          lineOffers {\n         " \
        "   appliedRules {\n              id\n              endDate\n              discountSetting {\n                " \
        "discountType\n              }\n            }\n          }\n        }\n        promotions(category: " \
        "$category) @include(if: $withPromotions) {\n          promotionalOffers {\n            promotionalOffers {\n " \
        "             startDate\n              endDate\n              discountSetting {\n                " \
        "discountType\n                discountPercentage\n              }\n            }\n          }\n          " \
        "upcomingPromotionalOffers {\n            promotionalOffers {\n              startDate\n              " \
        "endDate\n              discountSetting {\n                discountType\n                discountPercentage\n " \
        "             }\n            }\n          }\n        }\n      }\n      paging {\n        count\n        " \
        "total\n      }\n    }\n  }\n}\n "

import logging

from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtNetwork import QNetworkAccessManager
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

from rare.components.tabs.shop.constants import search_query
from rare.utils.extra_widgets import ImageLabel
from rare.utils.utils import get_lang, QtRequestManager

logger = logging.getLogger("GameWidgets")


class GameWidget(QWidget):
    show_info = pyqtSignal(dict)

    def __init__(self, path, json_info=None, width=300):
        super(GameWidget, self).__init__()
        self.manager = QNetworkAccessManager()
        self.width = width
        self.path = path
        if json_info:
            self.init_ui(json_info)

    def init_ui(self, json_info):
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
        c.manager = QtRequestManager("json")
        c.manager.data_ready.connect(c.handle_response)
        locale = get_lang()
        payload = {
            "query": search_query,
            "variables": {"category": "games/edition/base|bundles/games|editors|software/edition/base", "count": 1,
                          "country": "DE", "keywords": name, "locale": locale, "sortDir": "DESC",
                          "allowCountries": locale.upper(),
                          "start": 0, "tag": "", "withMapping": False, "withPrice": True}
        }
        c.manager.post("https://www.epicgames.com/graphql", payload)
        c.search_request.da.connect(lambda: c.handle_response(path))
        return c

    def handle_response(self, data):

        data = data["data"]["Catalog"]["searchStore"]["elements"][0]
        self.init_ui(data)

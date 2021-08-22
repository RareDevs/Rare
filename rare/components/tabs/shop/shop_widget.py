import datetime
import logging

from PyQt5.QtCore import Qt, pyqtSignal, QStringListModel
from PyQt5.QtNetwork import QNetworkAccessManager
from PyQt5.QtWidgets import QWidget, QCompleter, QGroupBox, QHBoxLayout, QScrollArea

from custom_legendary.core import LegendaryCore
from rare.components.tabs.shop import ShopApiCore
from rare.components.tabs.shop.constants import search_query
from rare.components.tabs.shop.game_widgets import GameWidget, GameWidgetDiscount
from rare.ui.components.tabs.store.store import Ui_ShopWidget
from rare.utils.extra_widgets import WaitingSpinner, FlowLayout, ButtonLineEdit
from rare.utils.utils import get_lang

logger = logging.getLogger("Shop")


# noinspection PyAttributeOutsideInit,PyBroadException
class ShopWidget(QScrollArea, Ui_ShopWidget):
    show_info = pyqtSignal(str)
    show_game = pyqtSignal(dict)
    free_game_widgets = []
    active_search_request = False
    next_search = ""
    wishlist: list = []

    def __init__(self, path, core: LegendaryCore, shop_api: ShopApiCore):
        super(ShopWidget, self).__init__()
        self.setWidgetResizable(True)
        self.setupUi(self)
        self.path = path
        self.core = core
        self.shop_api = shop_api
        self.manager = QNetworkAccessManager()
        self.free_games_widget = QWidget()
        self.free_games_widget.setLayout(FlowLayout())
        self.free_games_now = QGroupBox(self.tr("Free Games"))
        self.free_games_now.setLayout(QHBoxLayout())
        self.free_games_widget.layout().addWidget(self.free_games_now)
        self.coming_free_games = QGroupBox(self.tr("Free Games next week"))
        self.coming_free_games.setLayout(QHBoxLayout())
        self.free_games_widget.layout().addWidget(self.coming_free_games)
        self.free_games_stack.addWidget(WaitingSpinner())
        self.free_games_stack.addWidget(self.free_games_widget)

        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)

        self.data = []

        self.search_bar = ButtonLineEdit("fa.search", placeholder_text=self.tr("Search Games"))
        self.scrollAreaWidgetContents.layout().insertWidget(0, self.search_bar)

        # self.search_bar.textChanged.connect(self.search_games)

        self.search_bar.setCompleter(self.completer)
        self.search_bar.returnPressed.connect(self.show_search_results)
        self.search_bar.buttonClicked.connect(self.show_search_results)

        # self.search_bar.textChanged.connect(self.load_completer)
        self.wishlist_gb.setLayout(FlowLayout())
        self.wishlist_gb.setVisible(False)
        self.locale = get_lang()

    def load_completer(self, text):
        if text != "":

            payload = {
                "query": search_query,
                "variables": {"category": "games/edition/base|bundles/games|editors|software/edition/base",
                              "count": 20,
                              "country": self.locale.upper(), "keywords": text, "locale": self.locale,
                              "sortDir": "DESC",
                              "allowCountries": self.locale.upper(),
                              "start": 0, "tag": "", "withMapping": False, "withPrice": True}
            }
            self.search_request_manager.post("https://www.epicgames.com/graphql", payload)

    def load(self):
        # load free games
        self.shop_api.get_free_games(self.add_free_games)
        # load wishlist
        self.shop_api.get_wishlist(self.add_wishlist_items)

    def update_wishlist(self):
        self.shop_api.get_wishlist(self.add_wishlist_items)

    def add_wishlist_items(self, wishlist):
        QWidget().setLayout(self.wishlist_gb.layout())

        self.wishlist_gb.setLayout(FlowLayout())
        discounts = 0
        for game in wishlist:
            if game["offer"]["price"]["totalPrice"]["discount"] > 0:
                w = GameWidgetDiscount(self.path, game["offer"])
                w.show_info.connect(self.show_game.emit)
                self.wishlist_gb.layout().addWidget(w)
                discounts += 1
        self.wishlist_gb.setVisible(discounts > 0)

    def add_free_games(self, free_games):
        date = datetime.datetime.now()
        free_games_now = []
        coming_free_games = []
        for game in free_games:
            if game["title"] == "Mystery Game":
                coming_free_games.append(game)
                continue
            try:
                # parse datetime
                try:
                    end_date = datetime.datetime.strptime(
                        game["promotions"]["upcomingPromotionalOffers"][0]["promotionalOffers"][0]["endDate"],
                        '%Y-%m-%dT%H:%M:%S.%fZ')
                except Exception:
                    try:
                        end_date = datetime.datetime.strptime(
                            game["promotions"]["promotionalOffers"][0]["promotionalOffers"][0]["endDate"],
                            '%Y-%m-%dT%H:%M:%S.%fZ')
                    except Exception:
                        continue
                try:
                    start_date = datetime.datetime.strptime(
                        game["promotions"]["upcomingPromotionalOffers"][0]["promotionalOffers"][0]["startDate"],
                        '%Y-%m-%dT%H:%M:%S.%fZ')
                except Exception:
                    try:
                        start_date = datetime.datetime.strptime(
                            game["promotions"]["promotionalOffers"][0]["promotionalOffers"][0]["startDate"],
                            '%Y-%m-%dT%H:%M:%S.%fZ')
                    except Exception as e:
                        print(e)
                        continue

            except TypeError:
                print("type error")
                continue
            if start_date < date < end_date:
                free_games_now.append(game)
            elif start_date > date:
                coming_free_games.append(game)

        for free_game in free_games_now:
            w = GameWidget(self.path, free_game)
            w.show_info.connect(self.show_game.emit)
            self.free_games_now.layout().addWidget(w)
            self.free_game_widgets.append(w)

        self.free_games_now.layout().addStretch(1)
        for free_game in coming_free_games:
            w = GameWidget(self.path, free_game)
            if free_game["title"] != "Mystery Game":
                w.show_info.connect(self.show_game.emit)
            self.coming_free_games.layout().addWidget(w)
            self.free_game_widgets.append(w)
        self.coming_free_games.layout().addStretch(1)
        # self.coming_free_games.setFixedWidth(int(40 + len(coming_free_games) * 300))
        self.free_games_stack.setCurrentIndex(1)

    def set_completer(self, search_data):
        search_data = search_data["data"]["Catalog"]["searchStore"]["elements"]
        titles = [i.get("title") for i in search_data]
        model = QStringListModel()
        model.setStringList(titles)
        self.completer.setModel(model)

    def show_search_results(self):
        self.show_info.emit(self.search_bar.text())

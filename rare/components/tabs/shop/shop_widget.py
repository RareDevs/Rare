import datetime
import logging
import random

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QGroupBox, QScrollArea, QCheckBox, QLabel, QPushButton, QHBoxLayout

from legendary.core import LegendaryCore
from rare.ui.components.tabs.store.store import Ui_ShopWidget
from rare.utils.extra_widgets import WaitingSpinner, FlowLayout, ButtonLineEdit
from .constants import Constants
from .game_widgets import GameWidget
from .shop_api_core import ShopApiCore
from .shop_models import BrowseModel

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
        self.api_core = shop_api
        self.price = ""
        self.tags = []
        self.types = []
        self.update_games_allowed = True
        self.free_widget.setLayout(FlowLayout())

        self.free_stack.addWidget(WaitingSpinner())
        self.free_stack.setCurrentIndex(1)

        self.discount_widget.setLayout(FlowLayout())
        self.discount_stack.addWidget(WaitingSpinner())
        self.discount_stack.setCurrentIndex(1)

        self.game_widget.setLayout(FlowLayout())
        self.game_stack.addWidget(WaitingSpinner())
        self.game_stack.setCurrentIndex(1)

        self.search_bar = ButtonLineEdit("fa.search", placeholder_text=self.tr("Search Games"))
        self.layout().insertWidget(0, self.search_bar)

        # self.search_bar.textChanged.connect(self.search_games)

        self.search_bar.returnPressed.connect(self.show_search_results)
        self.search_bar.buttonClicked.connect(self.show_search_results)

        self.init_filter()

        # self.search_bar.textChanged.connect(self.load_completer)

    def load(self):
        # load free games
        self.api_core.get_free_games(self.add_free_games)
        # load wishlist
        self.api_core.get_wishlist(self.add_wishlist_items)
        # load browse games
        self.prepare_request()

    def update_wishlist(self):
        self.api_core.get_wishlist(self.add_wishlist_items)

    def add_wishlist_items(self, wishlist):
        for i in range(self.discount_widget.layout().count()):
            item = self.discount_widget.layout().itemAt(i)
            if item:
                item.widget().deleteLater()
        if wishlist and wishlist[0] == "error":
            self.discount_widget.layout().addWidget(QLabel(self.tr("Failed to get wishlist: ") + wishlist[1]))
            btn = QPushButton(self.tr("Reload"))
            self.discount_widget.layout().addWidget(btn)
            btn.clicked.connect(lambda: self.api_core.get_wishlist(self.add_wishlist_items))
            self.discount_stack.setCurrentIndex(0)
            return

        discounts = 0
        for game in wishlist:
            if not game:
                continue
            try:
                if game["offer"]["price"]["totalPrice"]["discount"] > 0:
                    w = GameWidget(self.path, game["offer"])
                    w.show_info.connect(self.show_game.emit)
                    self.discount_widget.layout().addWidget(w)
                    discounts += 1
            except Exception as e:
                logger.warning(str(game) + str(e))
                continue
        self.discounts_gb.setVisible(discounts > 0)
        self.discount_widget.update()
        self.discount_stack.setCurrentIndex(0)

    def add_free_games(self, free_games: list):
        for i in range(self.free_widget.layout().count()):
            item = self.free_widget.layout().itemAt(i)
            if item:
                item.widget().deleteLater()

        if free_games and free_games[0] == "error":
            self.free_widget.layout().addWidget(QLabel(self.tr("Failed to fetch free games: ") + free_games[1]))
            btn = QPushButton(self.tr("Reload"))
            self.free_widget.layout().addWidget(btn)
            btn.clicked.connect(lambda: self.api_core.get_free_games(self.add_free_games))
            self.free_stack.setCurrentIndex(0)
            return

        self.free_games_now = QGroupBox(self.tr("Now Free"))
        self.free_games_now.setLayout(QHBoxLayout())
        self.free_widget.layout().addWidget(self.free_games_now)

        self.coming_free_games = QGroupBox(self.tr("Free Games next week"))
        self.coming_free_games.setLayout(QHBoxLayout())
        self.free_widget.layout().addWidget(self.coming_free_games)

        date = datetime.datetime.now()
        free_games_now = []
        coming_free_games = []
        for game in free_games:
            try:
                if game['price']['totalPrice']['fmtPrice']['discountPrice'] == "0" and \
                        game['price']['totalPrice']['fmtPrice']['originalPrice'] != \
                        game['price']['totalPrice']['fmtPrice']['discountPrice']:
                    free_games_now.append(game)
                    continue

                if game["title"] == "Mystery Game":
                    coming_free_games.append(game)
                    continue
            except KeyError as e:
                logger.warning(str(e))

            try:
                # parse datetime to check if game is next week or now
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

                        continue

            except TypeError:
                print("type error")
                continue

            if start_date > date:
                coming_free_games.append(game)
        # free games now
        for free_game in free_games_now:
            w = GameWidget(self.path, free_game)
            w.show_info.connect(self.show_game.emit)
            self.free_games_now.layout().addWidget(w)
            self.free_game_widgets.append(w)

        # free games next week
        for free_game in coming_free_games:
            w = GameWidget(self.path, free_game)
            if free_game["title"] != "Mystery Game":
                w.show_info.connect(self.show_game.emit)
            self.coming_free_games.layout().addWidget(w)
        # self.coming_free_games.setFixedWidth(int(40 + len(coming_free_games) * 300))
        self.free_stack.setCurrentIndex(0)

    def show_search_results(self):
        self.show_info.emit(self.search_bar.text())

    def init_filter(self):

        self.none_price.toggled.connect(lambda: self.prepare_request("") if self.none_price.isChecked() else None)
        self.free_button.toggled.connect(lambda: self.prepare_request("free") if self.free_button.isChecked() else None)
        self.under10.toggled.connect(
            lambda: self.prepare_request("<price>[0, 1000)") if self.under10.isChecked() else None)
        self.under20.toggled.connect(
            lambda: self.prepare_request("<price>[0, 2000)") if self.under20.isChecked() else None)
        self.under30.toggled.connect(
            lambda: self.prepare_request("<price>[0, 3000)") if self.under30.isChecked() else None)
        self.above.toggled.connect(lambda: self.prepare_request("<price>[1499,]") if self.above.isChecked() else None)
        # self.on_discount.toggled.connect(lambda: self.prepare_request("sale") if self.on_discount.isChecked() else None)
        self.on_discount.toggled.connect(lambda: self.prepare_request())
        constants = Constants()

        self.checkboxes = []

        for groupbox, variables in [(self.genre_gb, constants.categories),
                                    (self.platform_gb, constants.platforms),
                                    (self.others_gb, constants.others),
                                    (self.type_gb, constants.types)]:

            for text, tag in variables:
                checkbox = CheckBox(text, tag)
                checkbox.activated.connect(lambda x: self.prepare_request(added_tag=x))
                checkbox.deactivated.connect(lambda x: self.prepare_request(removed_tag=x))
                groupbox.layout().addWidget(checkbox)
                self.checkboxes.append(checkbox)
        self.reset_button.clicked.connect(self.reset_filters)

    def reset_filters(self):
        self.update_games_allowed = False
        for cb in self.checkboxes:
            cb.setChecked(False)
        self.none_price.setChecked(True)

        self.tags = []
        self.types = []
        self.update_games_allowed = True
        self.prepare_request("")

        self.on_discount.setChecked(False)

    def prepare_request(self, price: str = None, added_tag: int = 0, removed_tag: int = 0,
                        added_type: str = "", removed_type: str = ""):
        if not self.update_games_allowed:
            return
        if price is not None:
            self.price = price

        if added_tag != 0:
            self.tags.append(added_tag)
        if removed_tag != 0 and removed_tag in self.tags:
            self.tags.remove(removed_tag)

        if added_type:
            self.types.append(added_type)
        if removed_type and removed_type in self.types:
            self.types.remove(removed_type)
        if (self.types or self.price) or self.tags or self.on_discount.isChecked():
            self.free_game_group_box.setVisible(False)
            self.discounts_gb.setVisible(False)
        else:
            self.free_game_group_box.setVisible(True)
            if len(self.discounts_gb.layout().children()) > 0:
                self.discounts_gb.setVisible(True)

        self.game_stack.setCurrentIndex(1)
        date = f"[,{datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%dT%X')}.{str(random.randint(0, 999)).zfill(3)}Z]"

        browse_model = BrowseModel(language_code=self.core.language_code, country_code=self.core.country_code,
                                   date=date, count=20, price=self.price,
                                   onSale=self.on_discount.isChecked())
        browse_model.tag = "|".join(self.tags)

        if self.types:
            browse_model.category = "|".join(self.types)
        self.api_core.browse_games(browse_model, self.show_games)

    def show_games(self, data):
        for item in (self.game_widget.layout().itemAt(i) for i in range(self.game_widget.layout().count())):
            item.widget().deleteLater()
        if data:
            for game in data:
                w = GameWidget(self.path, game, 275)
                self.game_widget.layout().addWidget(w)
                w.show_info.connect(self.show_game.emit)

        else:
            self.game_widget.layout().addWidget(
                QLabel(self.tr("Could not get games matching the filter")))
        self.game_stack.setCurrentIndex(0)

        self.game_widget.layout().update()


class CheckBox(QCheckBox):
    activated = pyqtSignal(str)
    deactivated = pyqtSignal(str)

    def __init__(self, text, tag):
        super(CheckBox, self).__init__(text)
        self.tag = tag

        self.toggled.connect(self.handle_toggle)

    def handle_toggle(self):
        if self.isChecked():
            self.activated.emit(self.tag)
        else:
            self.deactivated.emit(self.tag)

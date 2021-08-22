import datetime
import logging
import random

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QCheckBox, QVBoxLayout, QLabel

from rare.components.tabs.shop.constants import Constants
from rare.components.tabs.shop.game_widgets import GameWidget
from rare.components.tabs.shop.shop_models import BrowseModel
from rare.ui.components.tabs.store.browse_games import Ui_browse_games
from rare.utils.extra_widgets import FlowLayout, WaitingSpinner
from rare.utils.utils import get_lang

logger = logging.getLogger("BrowseGames")


class BrowseGames(QWidget, Ui_browse_games):
    show_game = pyqtSignal(dict)
    init = False
    price = ""
    tags = []
    types = []

    def __init__(self, path, api_core):
        super(BrowseGames, self).__init__()
        self.setupUi(self)
        self.api_core = api_core
        self.path = path
        self.games_widget = QWidget()
        self.games_widget.setLayout(FlowLayout())
        self.games.setWidget(self.games_widget)

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

        constants = Constants()

        for groupbox, variables in [(self.genre_gb, constants.categories),
                                    (self.platform_gb, constants.platforms),
                                    (self.others_gb, constants.others)]:

            for text, tag in variables:
                checkbox = CheckBox(text, tag)
                checkbox.activated.connect(lambda x: self.prepare_request(added_tag=x))
                checkbox.deactivated.connect(lambda x: self.prepare_request(removed_tag=x))
                groupbox.layout().addWidget(checkbox)

        for text, tag in constants.types:
            checkbox = CheckBox(text, tag)
            checkbox.activated.connect(lambda x: self.prepare_request(added_type=x))
            checkbox.deactivated.connect(lambda x: self.prepare_request(removed_type=x))
            self.type_gb.layout().addWidget(checkbox)

    def load(self):
        if not self.init:
            self.prepare_request()
            self.init = True

    def prepare_request(self, price: str = None, added_tag: int = 0, removed_tag: int = 0,
                        added_type: str = "", removed_type: str = ""):

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

        locale = get_lang()
        self.stack.setCurrentIndex(2)
        date = f"[,{datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%dT%X')}.{str(random.randint(0, 999)).zfill(3)}Z]"

        browse_model = BrowseModel(locale=locale, date=date, count=30, price=self.price)
        browse_model.tag = "|".join(self.tags)

        if self.types:
            browse_model.category = "|".join(self.types)

        self.api_core.browse_games(browse_model, self.show_games)

    def show_games(self, data):
        QWidget().setLayout(self.games_widget.layout())

        if data:
            self.games_widget.setLayout(FlowLayout())

            for game in data:
                w = GameWidget(self.path, game, 275)
                self.games_widget.layout().addWidget(w)
                w.show_info.connect(self.show_game.emit)

        else:
            self.games_widget.setLayout(QVBoxLayout())
            self.games_widget.layout().addWidget(
                QLabel(self.tr("Could not get games matching the filter")))
            self.games_widget.layout().addStretch(1)
        self.stack.setCurrentIndex(0)


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
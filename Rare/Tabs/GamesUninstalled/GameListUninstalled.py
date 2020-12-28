from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *

from Rare.Tabs.GamesUninstalled.GameWidget import UninstalledGameWidget
from legendary.core import LegendaryCore


class GameListUninstalled(QScrollArea):
    def __init__(self, parent, core: LegendaryCore):
        super(GameListUninstalled, self).__init__(parent=parent)
        self.widget = QWidget()
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.layout = QVBoxLayout()

        self.filter = QLineEdit()
        self.filter.textChanged.connect(self.filter_games)
        self.filter.setPlaceholderText("Filter Games")
        self.layout.addWidget(self.filter)

        self.widgets_uninstalled = []
        games = []
        installed = [i.app_name for i in core.get_installed_list()]
        for game in core.get_game_list():
            if not game.app_name in installed:
                games.append(game)
        games = sorted(games, key=lambda x: x.app_title)
        for game in games:
            game_widget = UninstalledGameWidget(game)
            self.layout.addWidget(game_widget)
            self.widgets_uninstalled.append(game_widget)

        self.layout.addStretch(1)
        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)

    def filter_games(self):
        for i in self.widgets_uninstalled:
            if self.filter.text().lower() in i.game.app_title.lower() + i.game.app_name.lower():
                i.setVisible(True)
            else:
                i.setVisible(False)

from logging import getLogger

from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLineEdit
from legendary.core import LegendaryCore

from Rare.GameWidget import GameWidget, UninstalledGameWidget

logger = getLogger("TabWidgets")


class BrowserTab(QWebEngineView):
    def __init__(self, parent):
        super(BrowserTab, self).__init__(parent=parent)
        self.profile = QWebEngineProfile("storage", self)
        self.webpage = QWebEnginePage(self.profile, self)
        self.setPage(self.webpage)
        self.load(QUrl("https://www.epicgames.com/store/"))
        self.show()

    def createWindow(self, QWebEnginePage_WebWindowType):
        return self


class GameListInstalled(QScrollArea):
    def __init__(self, parent, core: LegendaryCore):
        super(GameListInstalled, self).__init__(parent=parent)
        self.widget = QWidget()
        self.core = core
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.layout = QVBoxLayout()
        self.widgets = {}
        for i in sorted(core.get_installed_list(), key=lambda game: game.title):
            widget = GameWidget(i, core)
            widget.signal.connect(self.remove_game)
            self.widgets[i.app_name] = widget
            self.layout.addWidget(widget)
        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)

        # self.setLayout(self.layout)

    def remove_game(self, app_name: str):
        logger.info(f"Uninstall {app_name}")
        self.widgets[app_name].setVisible(False)
        self.layout.removeWidget(self.widgets[app_name])
        self.widgets[app_name].deleteLater()
        self.widgets.pop(app_name)


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

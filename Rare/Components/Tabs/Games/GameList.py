from PyQt5.QtCore import Qt, pyqtSignal, QSettings
from PyQt5.QtWidgets import *
from legendary.core import LegendaryCore

from Rare.Components.Tabs.Games.GameWidgetInstalled import GameWidgetInstalled
from Rare.Components.Tabs.Games.GameWidgetListUninstalled import UninstalledGameWidget
from Rare.Components.Tabs.Games.GameWidgetUninstalled import GameWidgetUninstalled
from Rare.Components.Tabs.Games.InstalledListWidget import GameWidget
from Rare.utils.Models import InstallOptions
from Rare.utils.QtExtensions import FlowLayout


class GameList(QScrollArea):
    install_game = pyqtSignal(InstallOptions)
    show_game_info = pyqtSignal(str)
    update_game = pyqtSignal()

    def __init__(self, core: LegendaryCore):
        super(GameList, self).__init__()
        self.core = core
        self.widgets = []
        self.setObjectName("list_widget")
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.settings = QSettings()
        icon_view = self.settings.value("icon_view", True, bool)
        self.init_ui(icon_view)

    def init_ui(self, icon_view=True):
        self.widget = QWidget()
        self.widgets = []
        if icon_view:
            self.layout = FlowLayout()
        else:
            self.layout = QVBoxLayout()
        self.updates = []

        # Installed Games
        for game in sorted(self.core.get_installed_list(), key=lambda x: x.title):
            if icon_view:
                widget = GameWidgetInstalled(self.core, game)
                widget.show_info.connect(lambda app_name: self.show_game_info.emit(app_name))
            else:
                widget = GameWidget(game, self.core)
            if widget.update_available:
                self.updates.append(widget.game.app_name)
                widget.update_game.connect(self.update_game.emit)
            self.layout.addWidget(widget)
            widget.update_list.connect(self.update_list)

        uninstalled_games = []
        installed = [i.app_name for i in self.core.get_installed_list()]
        # get Uninstalled games
        for game in sorted(self.core.get_game_list(), key=lambda x: x.app_title):
            if not game.app_name in installed:
                uninstalled_games.append(game)
        # add uninstalled to gui
        for game in uninstalled_games:
            if icon_view:
                widget = GameWidgetUninstalled(self.core, game)
            else:
                widget = UninstalledGameWidget(self.core, game)
            widget.install_game.connect(lambda options: self.install_game.emit(options))
            self.layout.addWidget(widget)
            self.widgets.append(widget)

        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)

    def filter(self, text: str):
        for w in self.widgets:
            if text.lower() in w.game.app_title.lower() + w.game.app_name.lower():
                w.setVisible(True)
            else:
                w.setVisible(False)

    def installed_only(self, i_o: bool):
        # TODO save state
        for w in self.widgets:
            w.setVisible(not i_o)

    def update_list(self, icon_view=True):
        print("Updating List")
        self.settings.setValue("icon_view", icon_view)
        self.setWidget(QWidget())
        self.init_ui(icon_view)
        self.update()

    def import_game(self):
        pass
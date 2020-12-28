from logging import getLogger

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *

from Rare.Tabs.GamesInstalled.GameWidget import GameWidget
from legendary.core import LegendaryCore

logger = getLogger("InstalledList")


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

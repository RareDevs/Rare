from logging import getLogger
from typing import List

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction

from rare.shared import GlobalSignalsSingleton
from rare.shared import LegendaryCoreSingleton
from rare.utils.meta import GameMeta

logger = getLogger("TrayIcon")


class TrayIcon(QSystemTrayIcon):
    # none:
    show_app: pyqtSignal = pyqtSignal()
    # int: exit code
    exit_app: pyqtSignal = pyqtSignal(int)

    def __init__(self, parent):
        super(TrayIcon, self).__init__(parent=parent)
        self.core = LegendaryCoreSingleton()

        self.setIcon(QIcon(":/images/Rare.png"))
        self.setVisible(True)
        self.setToolTip("Rare")

        self.menu = QMenu()

        self.show_action = QAction("Rare")
        self.show_action.triggered.connect(self.show_app)
        self.menu.addAction(self.show_action)

        self.menu.addSeparator()
        self.text_action = QAction("Quick launch")
        self.text_action.setEnabled(False)
        self.menu.addAction(self.text_action)

        if len(installed := self.core.get_installed_list()) < 5:
            last_played = [GameMeta(i.app_name) for i in sorted(installed, key=lambda x: x.title)]
        elif games := sorted(
                parent.tab_widget.games_tab.game_utils.game_meta.get_games(),
                key=lambda x: x.last_played, reverse=True):
            last_played: List[GameMeta] = games[0:5]
        else:
            last_played = [GameMeta(i.app_name) for i in sorted(installed, key=lambda x: x.title)][0:5]

        self.game_actions: List[QAction] = []

        for game in last_played:
            a = QAction(self.core.get_game(game.app_name).app_title)
            a.setProperty("app_name", game.app_name)
            self.game_actions.append(a)
            a.triggered.connect(
                lambda: parent.tab_widget.games_tab.game_utils.prepare_launch(
                    self.sender().property("app_name"))
            )

        self.menu.addActions(self.game_actions)
        self.menu.addSeparator()

        self.exit_action = QAction(self.tr("Quit"))
        self.exit_action.triggered.connect(lambda: self.exit_app.emit(0))
        self.menu.addAction(self.exit_action)
        self.setContextMenu(self.menu)

        self.signals = GlobalSignalsSingleton()
        self.signals.game_uninstalled.connect(self.remove_button)

    def remove_button(self, app_name: str):
        if action := next((i for i in self.game_actions if i.property("app_name") == app_name), None):
            self.game_actions.remove(action)
            action.deleteLater()

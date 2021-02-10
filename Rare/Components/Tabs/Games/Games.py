from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox

from Rare.Components.Tabs.Games.GameList import GameList


class Games(QWidget):
    def __init__(self, core):
        super(Games, self).__init__()
        self.layout = QVBoxLayout()

        self.head_bar = GameListHeadBar()
        self.game_list = GameList(core)

        self.layout.addLayout(self.head_bar)
        self.layout.addWidget(self.game_list)
        #self.layout.addStretch(1)
        self.setLayout(self.layout)


class GameListHeadBar(QHBoxLayout):
    def __init__(self):
        super(GameListHeadBar, self).__init__()
        self.installed_only = QCheckBox("Installed only")
        self.addWidget(self.installed_only)

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLineEdit, QLabel

from Rare.Components.Tabs.Games.GameList import GameList


class Games(QWidget):
    def __init__(self, core):
        super(Games, self).__init__()
        self.layout = QVBoxLayout()

        self.head_bar = GameListHeadBar()
        self.head_bar.setObjectName("head_bar")
        self.game_list = GameList(core)


        self.head_bar.search_bar.textChanged.connect(
            lambda: self.game_list.filter(self.head_bar.search_bar.text()))

        self.head_bar.installed_only.stateChanged.connect(lambda :
                                                          self.game_list.installed_only(self.head_bar.installed_only.isChecked()))

        self.layout.addWidget(self.head_bar)
        self.layout.addWidget(self.game_list)
        # self.layout.addStretch(1)
        self.setLayout(self.layout)


class GameListHeadBar(QWidget):
    def __init__(self):
        super(GameListHeadBar, self).__init__()
        self.layout = QHBoxLayout()

        self.installed_only = QCheckBox("Installed only")
        self.layout.addWidget(self.installed_only)

        self.layout.addStretch()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search Game")
        self.layout.addWidget(self.search_bar)

        self.layout.addStretch()
        self.list_view = QLabel("List view")
        self.layout.addWidget(self.list_view)
        self.view = QCheckBox("Icon view")
        self.layout.addWidget(self.view)

        self.setLayout(self.layout)

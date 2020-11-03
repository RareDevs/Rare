from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QLineEdit, QPushButton

from Rare.GameWidget import GameWidget, UninstalledGameWidget
from Rare.utils.legendaryUtils import get_installed, get_not_installed, logout


class BrowserTab(QWebEngineView):
    def __init__(self, parent):
        super(BrowserTab, self).__init__(parent=parent)
        self.load(QUrl("https://www.epicgames.com/store/"))
        self.show()


class Settings(QWidget):
    def __init__(self, parent):
        super(Settings, self).__init__(parent=parent)
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("<h1>Rare Settings</h1>"))
        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.logout)
        self.layout.addWidget(self.logout_button)

        self.layout.addStretch(1)
        self.setLayout(self.layout)

    def logout(self):
        logout()
        exit(0)


class GameListInstalled(QScrollArea):
    def __init__(self, parent):
        super(GameListInstalled, self).__init__(parent=parent)
        self.widget = QWidget()
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.layout = QVBoxLayout()
        for i in get_installed():
            widget = GameWidget(i)

            self.layout.addWidget(widget)
        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)


class GameListUninstalled(QScrollArea):
    def __init__(self, parent):
        super(GameListUninstalled, self).__init__(parent=parent)
        self.widget = QWidget()
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.layout = QVBoxLayout()

        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Search game TODO")
        self.layout.addWidget(self.filter)

        self.widgets = []
        for game in get_not_installed():
            game_widget = UninstalledGameWidget(game)
            self.layout.addWidget(game_widget)
            self.widgets.append(game_widget)
        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)


class UpdateList(QWidget):
    def __init__(self, parent):
        super(UpdateList, self).__init__(parent=parent)
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("Updates"))
        self.setLayout(self.layout)

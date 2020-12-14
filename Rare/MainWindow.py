from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget

from Rare.TabWidgets import GameListInstalled, GameListUninstalled, UpdateList, BrowserTab, Settings


class MainWindow(QMainWindow):

    def __init__(self, core):
        super().__init__()
        self.setWindowTitle("Rare - GUI for legendary-gl")
        self.setGeometry(0, 0, 1200, 900)
        self.setCentralWidget(TabWidget(self, core))
        self.show()


class TabWidget(QTabWidget):

    def __init__(self, parent, core):
        super(QWidget, self).__init__(parent)

        self.game_list = GameListInstalled(self, core)
        self.addTab(self.game_list, "Games")

        self.uninstalled_games = GameListUninstalled(self, core)
        self.addTab(self.uninstalled_games, "Install Games")

        self.update_tab = UpdateList(self, core)
        self.addTab(self.update_tab, "Updates")

        self.browser = BrowserTab(self)
        self.addTab(self.browser, "Store")

        self.settings = Settings(self)
        self.addTab(self.settings, "Settings")

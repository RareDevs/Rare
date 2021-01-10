from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget

from Rare.Tabs import SettingsTab, UpdateTab, GameListInstalled,GameListUninstalled, BrowserTab


class MainWindow(QMainWindow):

    def __init__(self, core):
        super().__init__()
        self.setWindowTitle("Rare - GUI for legendary-gl")
        self.setGeometry(0, 0, 1200, 900)
        self.setCentralWidget(TabWidget(core))
        self.show()


class TabWidget(QTabWidget):

    def __init__(self, core):
        super(QWidget, self).__init__()

        self.game_list = GameListInstalled(core)
        self.addTab(self.game_list, "Games")

        self.uninstalled_games = GameListUninstalled(core)
        self.addTab(self.uninstalled_games, "Install Games")

        self.update_tab = UpdateTab(core)
        self.addTab(self.update_tab, "Updates")

        self.browser = BrowserTab()
        self.addTab(self.browser, "Store")

        self.settings = SettingsTab(core)
        self.addTab(self.settings, "Settings")

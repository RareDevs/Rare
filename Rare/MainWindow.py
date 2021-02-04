from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget

from Rare.Tabs import SettingsTab, UpdateTab, GameListInstalled, GameListUninstalled, BrowserTab


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
        self.addTab(self.game_list, self.tr("Games"))
        self.uninstalled_games = GameListUninstalled(core)
        self.uninstalled_games.reload.connect(lambda: self.game_list.update_list())
        self.addTab(self.uninstalled_games, self.tr("Install Games"))

        self.update_tab = UpdateTab(core)
        self.addTab(self.update_tab, self.tr("Updates"))

        self.browser = BrowserTab()
        self.addTab(self.browser, self.tr("Website"))

        self.settings = SettingsTab(core)
        self.addTab(self.settings, self.tr("Settings"))
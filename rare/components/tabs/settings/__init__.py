from rare.shared import ArgumentsSingleton
from rare.widgets.side_tab import SideTabWidget
from .about import About
from .debug import DebugSettings
from .settings import GameSettings
from .legendary import LegendarySettings
from .rare import RareSettings


class SettingsTab(SideTabWidget):
    def __init__(self, parent=None):
        super(SettingsTab, self).__init__(parent=parent)
        self.args = ArgumentsSingleton()

        rare_settings = RareSettings(self)
        self.rare_index = self.addTab(rare_settings, "Rare")

        legendary_settings = LegendarySettings(self)
        self.legendary_index = self.addTab(legendary_settings, "Legendary")

        game_settings = GameSettings(self)
        self.settings_index = self.addTab(game_settings, self.tr("Defaults"))

        self.about = About(self)
        title = self.tr("About")
        self.about_index = self.addTab(self.about, title, title)
        self.about.update_available_ready.connect(
            lambda: self.tabBar().setTabText(self.about_index, "About (!)")
        )

        if self.args.debug:
            title = self.tr("Debug")
            self.debug_index = self.addTab(DebugSettings(self), title, title)

        self.setCurrentIndex(self.rare_index)

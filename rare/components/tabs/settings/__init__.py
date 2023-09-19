from rare.components.tabs.settings.widgets.wine import LinuxSettings
from rare.shared import ArgumentsSingleton
from rare.widgets.side_tab import SideTabWidget
from .about import About
from .debug import DebugSettings
from .game import DefaultGameSettings
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

        game_settings = DefaultGameSettings(True, self)
        self.settings_index = self.addTab(game_settings, self.tr("Defaults"))

        self.about = About(self)
        self.about_index = self.addTab(self.about, "About", "About")
        self.about.update_available_ready.connect(
            lambda: self.tabBar().setTabText(self.about_index, "About (!)")
        )

        if self.args.debug:
            self.debug_index = self.addTab(DebugSettings(self), "Debug")

        self.setCurrentIndex(self.rare_index)

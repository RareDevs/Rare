from rare.components.tabs.settings.widgets.linux import LinuxSettings
from rare.shared import ArgumentsSingleton
from rare.widgets.side_tab import SideTabWidget
from .about import About
from .debug import DebugSettings
from .game_settings import DefaultGameSettings
from .legendary import LegendarySettings
from .rare import RareSettings


class SettingsTab(SideTabWidget):
    def __init__(self, parent=None):
        super(SettingsTab, self).__init__(parent=parent)
        self.args = ArgumentsSingleton()

        self.rare_index = self.addTab(RareSettings(self), "Rare")
        self.legendary_index = self.addTab(LegendarySettings(self), "Legendary")
        self.settings_index = self.addTab(DefaultGameSettings(True, self), self.tr("Default Settings"))

        self.about = About(self)
        self.about_index = self.addTab(self.about, "About", "About")
        self.about.update_available_ready.connect(
            lambda: self.tabBar().setTabText(self.about_index, "About (!)")
        )

        if self.args.debug:
            self.debug_index = self.addTab(DebugSettings(self), "Debug")

        self.setCurrentIndex(self.rare_index)

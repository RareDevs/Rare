from rare.components.tabs.settings.widgets.linux import LinuxSettings
from rare.utils.extra_widgets import SideTabWidget
from .about import About
from .default_game_settings import DefaultGameSettings
from .legendary import LegendarySettings
from .rare import RareSettings


class SettingsTab(SideTabWidget):
    def __init__(self, parent=None):
        super(SettingsTab, self).__init__(parent=parent)
        about_tab = 3
        self.rare_settings = RareSettings()
        self.addTab(self.rare_settings, "Rare")

        self.addTab(LegendarySettings(), "Legendary")

        self.addTab(DefaultGameSettings(True, self), self.tr("Default Settings"))

        self.about = About()
        self.addTab(self.about, "About", "About")
        self.about.update_available_ready.connect(
            lambda: self.tabBar().setTabText(about_tab, "About (!)")
        )

        self.setCurrentIndex(0)

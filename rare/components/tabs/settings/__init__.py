import platform

from rare import shared
from rare.utils.extra_widgets import SideTabWidget
from .about import About
from .legendary import LegendarySettings
from .linux import LinuxSettings
from .rare import RareSettings


class SettingsTab(SideTabWidget):
    def __init__(self, parent=None):
        super(SettingsTab, self).__init__(parent=parent)

        self.rare_settings = RareSettings()
        self.addTab(self.rare_settings, "Rare")

        self.addTab(LegendarySettings(), "Legendary")

        if platform.system() != "Windows":
            self.addTab(LinuxSettings(), "Linux")

        self.about = About()
        self.addTab(self.about, "About (!)" if self.about.update_available else "About")

        self.setCurrentIndex(0)
        print(shared.api_results.saves)

import platform

from rare.utils.extra_widgets import SideTabWidget
from .about import About
from .legendary import LegendarySettings
from .linux import LinuxSettings
from .rare import RareSettings


class SettingsTab(SideTabWidget):
    def __init__(self, parent=None):
        super(SettingsTab, self).__init__(parent=parent)
        about_tab = 2
        self.rare_settings = RareSettings()
        self.addTab(self.rare_settings, "Rare")

        self.addTab(LegendarySettings(), "Legendary")

        if platform.system() != "Windows":
            self.addTab(LinuxSettings(), "Linux")
            about_tab = 3

        self.about = About()
        self.addTab(self.about, "About")
        self.about.update_available_ready.connect(lambda: self.tabBar().setTabText(about_tab, "About (!)"))

        self.setCurrentIndex(0)

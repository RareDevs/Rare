import os

from PyQt5.QtWidgets import QTabWidget

from rare.components.tabs.Settings.about import About
from rare.components.tabs.Settings.legendary import LegendarySettings
from rare.components.tabs.Settings.linux import LinuxSettings
from rare.components.tabs.Settings.rare import RareSettings
from rare.utils.extra_widgets import SideTabBar


class SettingsTab(QTabWidget):
    def __init__(self, core):
        super(SettingsTab, self).__init__()
        self.core = core
        self.setTabBar(SideTabBar())
        self.setTabPosition(QTabWidget.West)
        self.addTab(RareSettings(), "Rare")
        self.addTab(LegendarySettings(core), "Legendary")
        if os.name != "nt":
            self.addTab(LinuxSettings(core), "Linux")
        self.about = About()

        self.addTab(self.about, "About (!)" if self.about.update_available else "About")

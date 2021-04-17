import os

from PyQt5.QtWidgets import QTabWidget

from rare.components.tabs.settings.about import About
from rare.components.tabs.settings.legendary import LegendarySettings
from rare.components.tabs.settings.linux import LinuxSettings
from rare.components.tabs.settings.rare import RareSettings
from rare.utils.extra_widgets import SideTabBar


class SettingsTab(QTabWidget):
    def __init__(self, core, parent):
        super(SettingsTab, self).__init__(parent=parent)
        self.core = core
        self.setTabBar(SideTabBar())
        self.setTabPosition(QTabWidget.West)
        self.rare_settings = RareSettings()
        self.addTab(self.rare_settings, "Rare")
        self.addTab(LegendarySettings(core), "Legendary")
        if os.name != "nt":
            self.addTab(LinuxSettings(core), "Linux")
        self.about = About()

        self.addTab(self.about, "About (!)" if self.about.update_available else "About")

import os

from PyQt5.QtCore import QRect, QPoint, QSize
from PyQt5.QtWidgets import QTabWidget, QStylePainter, QStyleOptionTab, QTabBar, QStyle

from Rare.Components.Tabs.Settings.About import About
from Rare.Components.Tabs.Settings.Legendary import LegendarySettings
from Rare.Components.Tabs.Settings.Linux import LinuxSettings
from Rare.Components.Tabs.Settings.Rare import RareSettings
from Rare.utils.QtExtensions import SideTabBar


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
        self.addTab(About(), "About")


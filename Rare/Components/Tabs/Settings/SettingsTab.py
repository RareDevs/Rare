import os

from PyQt5.QtCore import QRect, QPoint, QSize
from PyQt5.QtWidgets import QTabWidget, QStylePainter, QStyleOptionTab, QTabBar, QStyle

from Rare.Components.Tabs.Settings.About import About
from Rare.Components.Tabs.Settings.Legendary import LegendarySettings
from Rare.Components.Tabs.Settings.Linux import LinuxSettings
from Rare.Components.Tabs.Settings.Rare import RareSettings


class SettingsTab(QTabWidget):
    def __init__(self, core):
        super(SettingsTab, self).__init__()
        self.core = core
        self.setTabBar(TabBar())
        self.setTabPosition(QTabWidget.West)
        self.addTab(RareSettings(), "Rare")
        self.addTab(LegendarySettings(core), "Legendary")
        if os.name != "nt":
            self.addTab(LinuxSettings(core), "Linux")
        self.addTab(About(), "About")


class TabBar(QTabBar):
    def __init__(self):
        super(TabBar, self).__init__()
        self.setObjectName("settings_bar")

    def tabSizeHint(self, index):
        # width = QTabBar.tabSizeHint(self, index).width()
        return QSize(200, 30)

    def paintEvent(self, event):
        painter = QStylePainter(self)
        opt = QStyleOptionTab()

        for i in range(self.count()):
            self.initStyleOption(opt, i)
            painter.drawControl(QStyle.CE_TabBarTabShape, opt)
            painter.save()

            s = opt.rect.size()
            s.transpose()
            r = QRect(QPoint(), s)
            r.moveCenter(opt.rect.center())
            opt.rect = r

            c = self.tabRect(i).center()
            painter.translate(c)
            painter.rotate(90)
            painter.translate(-c)
            painter.drawControl(QStyle.CE_TabBarTabLabel, opt);
            painter.restore()

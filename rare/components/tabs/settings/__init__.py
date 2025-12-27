import platform as pf

from PySide6.QtCore import Signal, Slot

from rare.models.settings import RareAppSettings
from rare.shared import RareCore
from rare.widgets.side_tab import SideTabWidget

from .about import About
from .compat import GlobalCompatSettings
from .debug import DebugSettings
from .game import GlobalGameSettings
from .legendary import LegendarySettings
from .rare import RareSettings


class SettingsTab(SideTabWidget):
    update_available = Signal()

    def __init__(self, settings: RareAppSettings, rcore: RareCore, parent=None):
        super(SettingsTab, self).__init__(parent=parent)

        rare_settings = RareSettings(settings, rcore, self)
        self.rare_index = self.addTab(rare_settings, "Rare")

        legendary_settings = LegendarySettings(settings, rcore, self)
        self.legendary_index = self.addTab(legendary_settings, "Legendary")

        game_settings = GlobalGameSettings(settings, rcore, self)
        self.game_index = self.addTab(game_settings, self.tr("Defaults"))

        if pf.system() != "Windows":
            compat_settings = GlobalCompatSettings(settings, rcore, self)
            self.compat_index = self.addTab(compat_settings, self.tr("Compatibility"))

        self.about = About(self)
        title = self.tr("About")
        self.about_index = self.addTab(self.about, title, title)
        self.about.update_available.connect(self._on_update_available)
        self.about.update_available.connect(self.update_available)

        if rcore.args().debug:
            title = self.tr("Debug")
            self.debug_index = self.addTab(DebugSettings(rcore.signals(), self), title, title)

        self.setCurrentIndex(self.rare_index)

    @Slot()
    def _on_update_available(self):
        self.tabBar().setTabText(self.about_index, "About (!)")
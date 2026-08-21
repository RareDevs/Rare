from rare.shared import RareCore
from rare.widgets.scrollarea_tabs import ScrollAreaTabContents

from .widgets.envvars import EnvVars


class EnvironSettingsBase(EnvVars, ScrollAreaTabContents):
    def __init__(
        self,
        rcore: RareCore,
        parent=None,
    ):
        super(EnvironSettingsBase, self).__init__(rcore.core(), parent=parent)
        self.implements_scrollarea = True


class GlobalEnvironSettings(EnvironSettingsBase):
    def __init__(self, rcore: RareCore, parent=None):
        super(GlobalEnvironSettings, self).__init__(rcore, parent=parent)

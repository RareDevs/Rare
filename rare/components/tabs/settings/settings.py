import platform as pf
from logging import getLogger

from .widgets.env_vars import EnvVars
from .widgets.game import GameSettingsBase
from .widgets.launch import LaunchSettingsBase
from .widgets.overlay import DxvkSettings
from .widgets.wrappers import WrapperSettings

if pf.system() != "Windows":
    from .widgets.wine import WineSettings

if pf.system() not in {"Windows", "Darwin"}:
    from .widgets.proton import ProtonSettings
    from .widgets.overlay import MangoHudSettings

logger = getLogger("GameSettings")


class LaunchSettings(LaunchSettingsBase):
    def __init__(self, parent=None):
        super(LaunchSettings, self).__init__(WrapperSettings, parent=parent)


class GameSettings(GameSettingsBase):
    def __init__(self, parent=None):
        if pf.system() not in {"Windows", "Darwin"}:
            super(GameSettings, self).__init__(
                LaunchSettings, DxvkSettings, EnvVars,
                WineSettings, ProtonSettings, MangoHudSettings,
                parent=parent
            )
        elif pf.system() != "Windows":
            super(GameSettings, self).__init__(
                LaunchSettings, DxvkSettings, EnvVars,
                WineSettings,
                parent=parent
            )
        else:
            super(GameSettings, self).__init__(
                LaunchSettings, DxvkSettings, EnvVars,
                parent=parent
            )

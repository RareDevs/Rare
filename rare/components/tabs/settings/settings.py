from logging import getLogger

from .widgets.env_vars import EnvVars
from .widgets.game import GameSettingsBase
from .widgets.launch import LaunchSettingsBase
from .widgets.overlay import MangoHudSettings, DxvkSettings
from .widgets.proton import ProtonSettings
from .widgets.wine import WineSettings
from .widgets.wrappers import WrapperSettings

logger = getLogger("GameSettings")


class LaunchSettings(LaunchSettingsBase):
    def __init__(self, parent=None):
        super(LaunchSettings, self).__init__(WrapperSettings, parent=parent)


class GameSettings(GameSettingsBase):
    def __init__(self, parent=None):
        super(GameSettings, self).__init__(
            LaunchSettings, WineSettings, ProtonSettings, DxvkSettings, MangoHudSettings, EnvVars,
            parent=parent
        )

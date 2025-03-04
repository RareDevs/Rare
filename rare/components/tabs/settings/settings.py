import platform as pf
from logging import getLogger

from .widgets.env_vars import EnvVars
from .widgets.game import GameSettingsBase
from .widgets.launch import LaunchSettingsBase
from .widgets.overlay import DxvkSettings
from .widgets.wrappers import WrapperSettings

if pf.system() != "Windows":
    from .widgets.runner import RunnerSettingsBase
    from .widgets.wine import WineSettings
    if pf.system() in {"Linux", "FreeBSD"}:
        from .widgets.proton import ProtonSettings
        from .widgets.overlay import MangoHudSettings

logger = getLogger("GameSettings")


class LaunchSettings(LaunchSettingsBase):
    def __init__(self, parent=None):
        super(LaunchSettings, self).__init__(WrapperSettings, parent=parent)


if pf.system() != "Windows":
    class RunnerSettings(RunnerSettingsBase):
        def __init__(self, parent=None):
            if pf.system() in {"Linux", "FreeBSD"}:
                super(RunnerSettings, self).__init__(WineSettings, ProtonSettings, parent=parent)
            else:
                super(RunnerSettings, self).__init__(WineSettings, parent=parent)


class GameSettings(GameSettingsBase):
    def __init__(self, parent=None):
        if pf.system() != "Windows":
            if pf.system() in {"Linux", "FreeBSD"}:
                super(GameSettings, self).__init__(
                    launch_widget=LaunchSettings,
                    dxvk_widget=DxvkSettings,
                    envvar_widget=EnvVars,
                    runner_widget=RunnerSettings,
                    mangohud_widget=MangoHudSettings,
                    parent=parent
                )
            else:
                super(GameSettings, self).__init__(
                    launch_widget=LaunchSettings,
                    dxvk_widget=DxvkSettings,
                    envvar_widget=EnvVars,
                    runner_widget=RunnerSettings,
                    parent=parent
                )
        else:
            super(GameSettings, self).__init__(
                launch_widget=LaunchSettings,
                dxvk_widget=DxvkSettings,
                envvar_widget=EnvVars,
                parent=parent
            )

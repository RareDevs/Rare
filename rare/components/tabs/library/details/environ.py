from rare.components.tabs.settings.environ import EnvironSettingsBase
from rare.models.game import RareGame
from rare.shared import RareCore


class LocalEnvironSettings(EnvironSettingsBase):
    def __init__(self, rcore: RareCore, parent=None):
        super(LocalEnvironSettings, self).__init__(rcore, parent=parent)

    def load_settings(self, rgame: RareGame):
        self.set_title.emit(rgame.app_title)
        self.app_name = rgame.app_name

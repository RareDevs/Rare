import platform
import time

from PyQt5.QtCore import QObject, QSettings
from pypresence import Presence

from custom_legendary.core import LegendaryCore

client_id = "830732538225360908"


class DiscordRPC(QObject):
    def __init__(self, core: LegendaryCore):
        super(DiscordRPC, self).__init__()
        self.RPC = None
        self.state = 1  # 0: game, 1: always active, 2: off
        self.core = core
        self.settings = QSettings()
        if self.settings.value("rpc_enable", 0, int) == 1:  # show always
            self.state = 2
            self.set_discord_rpc()

    def changed_settings(self, game_running: list):
        value = self.settings.value("rpc_enable", 0, int)
        if value == 2:
            self.remove_rpc()
            return
        if not game_running:
            self.remove_rpc()
        else:
            self.set_discord_rpc(game_running[0])

    def remove_rpc(self):
        if self.settings.value("rpc_enable", 0, int) != 1:
            if not self.RPC:
                return
            self.RPC.close()
            del self.RPC
            self.RPC = None
            self.state = 2
        else:
            self.state = 1
            self.set_discord_rpc()

    def set_discord_rpc(self, app_name=None):
        if not self.RPC:
            self.RPC = Presence("830732538225360908")  # Rare app: https://discord.com/developers/applications
            self.RPC.connect()
        self.update_rpc(app_name)

    def update_rpc(self, app_name=None):
        if self.settings.value("rpc_enable", 0, int) == 2:
            self.remove_rpc()
            return
        title = None
        if not app_name:
            self.RPC.update(large_image="logo",
                            details="https://github.com/Dummerle/Rare")
            return
        if self.settings.value("rpc_name", True, bool):
            title = self.core.get_installed_game(app_name).title
        start = None
        if self.settings.value("rpc_time", True, bool):
            start = str(time.time()).split(".")[0]
        os = None
        if self.settings.value("rpc_os", True, bool):
            os = "via Rare on " + platform.system()

        self.RPC.update(large_image="logo",
                        details=title,
                        large_text=title,
                        state=os,
                        start=start)
        self.state = 0

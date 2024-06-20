import platform
import time
from logging import getLogger
from typing import List

from PySide6.QtCore import QObject, QSettings, Slot
from pypresence import Presence, exceptions

from rare.models.options import options
from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton

client_id = "830732538225360908"
logger = getLogger("DiscordRPC")


class DiscordRPC(QObject):
    def __init__(self):
        super(DiscordRPC, self).__init__()
        self.rpc = None
        self.state = 1  # 0: game, 1: always active, 2: off
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()

        self.settings = QSettings()
        if self.settings.value(*options.discord_rpc_mode) == 1:  # show always
            self.state = 2
            self.set_discord_rpc()

        self.signals.discord_rpc.update_presence.connect(self.update_presence)
        self.signals.discord_rpc.remove_presence.connect(self.remove_presence)
        self.signals.discord_rpc.update_settings.connect(self.update_settings)

    @Slot(str)
    def update_presence(self, app_name: str):
        self.set_discord_rpc(app_name)

    @Slot(str)
    def remove_presence(self, app_name: str):
        self.set_discord_rpc(None)

    @Slot()
    @Slot(list)
    def update_settings(self, game_running: List = None):
        value = self.settings.value(*options.discord_rpc_mode)
        if value == 2:
            self.remove_rpc()
            return
        if not game_running and value == 0:
            self.remove_rpc()
        elif not game_running:
            self.set_discord_rpc()
        else:
            self.set_discord_rpc(game_running[0])

    def remove_rpc(self):
        if self.settings.value(*options.discord_rpc_mode) != 1:
            if not self.rpc:
                return
            try:
                self.rpc.close()
            except Exception:
                logger.warning("Already closed")
            del self.rpc
            self.rpc = None
            logger.info("Remove RPC")
            self.state = 2
        else:
            self.state = 1
            self.set_discord_rpc()

    def set_discord_rpc(self, app_name=None):
        if not self.rpc:
            try:
                self.rpc = Presence(client_id)  # Rare app: https://discord.com/developers/applications
                self.rpc.connect()
            except ConnectionRefusedError as e:
                logger.warning(f"Discord is not active\n{e}")
                self.rpc = None
                return
            except FileNotFoundError as e:
                logger.warning(f"File not found error\n{e}")
                self.rpc = None
                return
            except exceptions.InvalidPipe as e:
                logger.error(f"Is Discord running? \n{e}")
                self.rpc = None
                return
            except Exception as e:
                logger.error(str(e))
                self.rpc = None
                return
        self.update_rpc(app_name)

    def update_rpc(self, app_name=None):
        if self.settings.value(*options.discord_rpc_mode) == 2 or (
            not app_name and self.settings.value(*options.discord_rpc_mode) == 0
        ):
            self.remove_rpc()
            return
        title = None
        if not app_name:
            self.rpc.update(large_image="logo", details="https://github.com/RareDevs/Rare")
            return
        if self.settings.value(*options.discord_rpc_game):
            try:
                title = self.core.get_installed_game(app_name).title
            except AttributeError:
                logger.error(f"Could not get title of game: {app_name}")
                title = app_name
        start = None
        if self.settings.value(*options.discord_rpc_time):
            start = str(time.time()).split(".")[0]
        os = None
        if self.settings.value(*options.discord_rpc_os):
            os = f"via Rare on {platform.system()}"

        self.rpc.update(large_image="logo", details=title, large_text=title, state=os, start=start)
        self.state = 0

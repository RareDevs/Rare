import platform
import time
from logging import getLogger

import pypresence.exceptions
from PyQt5.QtCore import QObject, QSettings
from pypresence import Presence

from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton

client_id = "830732538225360908"
logger = getLogger("RPC")


class DiscordRPC(QObject):
    def __init__(self):
        super(DiscordRPC, self).__init__()
        self.RPC = None
        self.state = 1  # 0: game, 1: always active, 2: off
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()

        self.settings = QSettings()
        if self.settings.value("rpc_enable", 0, int) == 1:  # show always
            self.state = 2
            self.set_discord_rpc()

        self.signals.discord_rpc.set_title.connect(self.update_presence)
        self.signals.discord_rpc.apply_settings.connect(self.changed_settings)

    def update_presence(self, app_name):
        self.set_discord_rpc(app_name)

    def changed_settings(self, game_running: list = None):
        value = self.settings.value("rpc_enable", 0, int)
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
        if self.settings.value("rpc_enable", 0, int) != 1:
            if not self.RPC:
                return
            try:
                self.RPC.close()
            except Exception:
                logger.warning("Already closed")
            del self.RPC
            self.RPC = None
            logger.info("Remove RPC")
            self.state = 2
        else:
            self.state = 1
            self.set_discord_rpc()

    def set_discord_rpc(self, app_name=None):
        if not self.RPC:
            try:
                self.RPC = Presence(
                    client_id
                )  # Rare app: https://discord.com/developers/applications
                self.RPC.connect()
            except ConnectionRefusedError as e:
                logger.warning(f"Discord is not active\n{e}")
                self.RPC = None
                return
            except FileNotFoundError as e:
                logger.warning(f"File not found error\n{e}")
                self.RPC = None
                return
            except pypresence.exceptions.InvalidPipe as e:
                logger.error(f"Is Discord running? \n{e}")
                self.RPC = None
                return
            except Exception as e:
                logger.error(str(e))
                self.RPC = None
                return
        self.update_rpc(app_name)

    def update_rpc(self, app_name=None):
        if self.settings.value("rpc_enable", 0, int) == 2 or (
                not app_name and self.settings.value("rpc_enable", 0, int) == 0
        ):
            self.remove_rpc()
            return
        title = None
        if not app_name:
            self.RPC.update(
                large_image="logo", details="https://github.com/Dummerle/Rare"
            )
            return
        if self.settings.value("rpc_name", True, bool):
            try:
                title = self.core.get_installed_game(app_name).title
            except AttributeError:
                logger.error(f"Could not get title of game: {app_name}")
                title = app_name
        start = None
        if self.settings.value("rpc_time", True, bool):
            start = str(time.time()).split(".")[0]
        os = None
        if self.settings.value("rpc_os", True, bool):
            os = f"via Rare on {platform.system()}"

        self.RPC.update(
            large_image="logo", details=title, large_text=title, state=os, start=start
        )
        self.state = 0

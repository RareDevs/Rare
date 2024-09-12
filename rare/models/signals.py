from PySide6.QtCore import QObject, Signal

from .install import InstallOptionsModel, UninstallOptionsModel


class GlobalSignals:

    # set_main_tab_index = Signal(int)  # tab index
    # update_gamelist = Signal(list)

    class ApplicationSignals(QObject):
        # int: exit code
        quit = Signal(int)
        # str: title, str: body
        notify = Signal(str, str)
        # none
        update_tray = Signal()
        # none
        update_statusbar = Signal()
        # str: locale
        # change_translation = Signal(str)

    class GameSignals(QObject):
        # model
        install = Signal(InstallOptionsModel)
        # str: app_name
        installed = Signal(str)
        # model
        uninstall = Signal(UninstallOptionsModel)
        # str: app_name
        uninstalled = Signal(str)

    class DownloadSignals(QObject):
        # str: app_name
        enqueue = Signal(str)
        # str: app_name
        dequeue = Signal(str)

    class DiscordRPCSignals(QObject):
        # str: app_name
        update_presence = Signal(str)
        # str: app_name
        remove_presence = Signal(str)
        # none
        update_settings = Signal()

    def __init__(self):
        self.application = GlobalSignals.ApplicationSignals()
        self.game = GlobalSignals.GameSignals()
        self.download = GlobalSignals.DownloadSignals()
        self.discord_rpc = GlobalSignals.DiscordRPCSignals()

    def deleteLater(self):
        self.application.deleteLater()
        del self.application
        self.game.deleteLater()
        del self.game
        self.download.deleteLater()
        del self.download
        self.discord_rpc.deleteLater()
        del self.discord_rpc

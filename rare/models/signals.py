from PySide6.QtCore import QObject, Signal

from .install import InstallOptionsModel, UninstallOptionsModel


class GlobalSignalsApplicationSignals(QObject):
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
    # none
    update_game_tags = Signal()


class GlobalSignalsGameSignals(QObject):
    # model
    install = Signal(InstallOptionsModel)
    # str: app_name
    installed = Signal(str)
    # model
    uninstall = Signal(UninstallOptionsModel)
    # str: app_name
    uninstalled = Signal(str)


class GlobalSignalsDownloadSignals(QObject):
    # str: app_name
    enqueue = Signal(str)
    # str: app_name
    dequeue = Signal(str)


class GlobalSignalsDiscordRPCSignals(QObject):
    # str: app_name
    update_presence = Signal(str)
    # str: app_name
    remove_presence = Signal(str)
    # none
    update_settings = Signal()


class GlobalSignals(QObject):

    def __init__(self):
        super(GlobalSignals, self).__init__()
        self.application = GlobalSignalsApplicationSignals()
        self.game = GlobalSignalsGameSignals()
        self.download = GlobalSignalsDownloadSignals()
        self.discord_rpc = GlobalSignalsDiscordRPCSignals()

    def deleteLater(self):
        self.application.disconnect(self.application)
        self.application.deleteLater()
        del self.application
        self.game.disconnect(self.game)
        self.game.deleteLater()
        del self.game
        self.download.disconnect(self.download)
        self.download.deleteLater()
        del self.download
        self.discord_rpc.disconnect(self.discord_rpc)
        self.discord_rpc.deleteLater()
        del self.discord_rpc
        super(GlobalSignals, self).deleteLater()

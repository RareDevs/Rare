from PyQt5.QtCore import QObject, pyqtSignal

from .install import InstallOptionsModel, UninstallOptionsModel


class GlobalSignals:

    # set_main_tab_index = pyqtSignal(int)  # tab index
    # update_gamelist = pyqtSignal(list)

    class ApplicationSignals(QObject):
        # int: exit code
        quit =  pyqtSignal(int)
        # str: app_title
        notify = pyqtSignal(str)
        # none
        prefix_updated = pyqtSignal()
        # none
        overlay_installed = pyqtSignal()
        # none
        update_tray = pyqtSignal()
        # none
        update_statusbar = pyqtSignal()

    class GameSignals(QObject):
        # model
        install = pyqtSignal(InstallOptionsModel)
        # str: app_name
        installed = pyqtSignal(str)
        # model
        uninstall = pyqtSignal(UninstallOptionsModel)
        # str: app_name
        uninstalled = pyqtSignal(str)

    class DownloadSignals(QObject):
        # str: app_name
        enqueue = pyqtSignal(str)
        # str: app_name
        dequeue = pyqtSignal(str)

    class DiscordRPCSignals(QObject):
        # str: app_title
        set_title = pyqtSignal(str)
        # none
        apply_settings = pyqtSignal()

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
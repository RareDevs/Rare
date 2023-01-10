from PyQt5.QtCore import QObject, pyqtSignal

from .install import InstallOptionsModel


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

    class ProgressSignals(QObject):
        # str: app_name
        started = pyqtSignal(str)
        # str: app_name, int: progress
        value = pyqtSignal(str, int)
        # str: app_name, bool: stopped
        finished = pyqtSignal(str, bool)

    class GameSignals(QObject):
        install = pyqtSignal(InstallOptionsModel)
        # list: app_name
        installed = pyqtSignal(list)
        # str: app_name
        uninstalled = pyqtSignal(str)
        # str: app_name
        verified = pyqtSignal(str)

    class DownloadSignals(QObject):
        # str: app_name
        enqueue_game = pyqtSignal(str)
        # none
        update_tab = pyqtSignal()

    class DiscordRPCSignals(QObject):
        # str: app_title
        set_title = pyqtSignal(str)
        # none
        apply_settings = pyqtSignal()

    def __init__(self):
        self.application = GlobalSignals.ApplicationSignals()
        self.progress = GlobalSignals.ProgressSignals()
        self.game = GlobalSignals.GameSignals()
        self.download = GlobalSignals.DownloadSignals()
        self.discord_rpc = GlobalSignals.DiscordRPCSignals()

    def deleteLater(self):
        self.application.deleteLater()
        del self.application
        self.progress.deleteLater()
        del self.progress
        self.game.deleteLater()
        del self.game
        self.download.deleteLater()
        del self.download
        self.discord_rpc.deleteLater()
        del self.discord_rpc
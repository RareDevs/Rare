from PyQt5.QtCore import QObject, pyqtSignal

from .install import InstallOptionsModel


class GlobalSignals(QObject):
    exit_app = pyqtSignal(int)  # exit code
    send_notification = pyqtSignal(str)  # app_title

    set_main_tab_index = pyqtSignal(int)  # tab index
    update_download_tab_text = pyqtSignal()

    class ProgressSignals(QObject):
        # str: app_name
        started = pyqtSignal(str)
        # str: app_name, int: progress
        value = pyqtSignal(str, int)
        # str: app_name, bool: stopped
        finished = pyqtSignal(str, bool)
    progress = ProgressSignals()

    class GameSignals(QObject):
        install = pyqtSignal(InstallOptionsModel)
        # list of app_name
        installed = pyqtSignal(list)
        # str: app_name
        uninstalled = pyqtSignal(str)
        # str: app_name
        verified = pyqtSignal(str)
    game = GameSignals()

    class DownloadSignals(QObject):
        # str: app_name
        enqueue_game = pyqtSignal(str)
    download = DownloadSignals()

    overlay_installation_finished = pyqtSignal()

    # update_gamelist = pyqtSignal(list)
    # game_uninstalled = pyqtSignal(str)

    set_discord_rpc = pyqtSignal(str)  # app_name of running game
    rpc_settings_updated = pyqtSignal()

    wine_prefix_updated = pyqtSignal()

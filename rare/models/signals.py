from PyQt5.QtCore import QObject, pyqtSignal

from .install import InstallOptionsModel


class GlobalSignals(QObject):
    exit_app = pyqtSignal(int)  # exit code
    send_notification = pyqtSignal(str)  # app_title

    set_main_tab_index = pyqtSignal(int)  # tab index
    update_download_tab_text = pyqtSignal()

    dl_progress = pyqtSignal(int)  # 0-100
    # set visibility of installing widget in games tab
    installation_started = pyqtSignal(str)  # app_name
    add_download = pyqtSignal(str)

    install_game = pyqtSignal(InstallOptionsModel)
    installation_finished = pyqtSignal(bool, str)

    overlay_installation_finished = pyqtSignal()

    update_gamelist = pyqtSignal(list)
    game_uninstalled = pyqtSignal(str)  # appname

    set_discord_rpc = pyqtSignal(str)  # app_name of running game
    rpc_settings_updated = pyqtSignal()

    wine_prefix_updated = pyqtSignal()

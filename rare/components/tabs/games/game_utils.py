import os
import platform
import shutil
import webbrowser
from dataclasses import dataclass
from logging import getLogger

from PyQt5.QtCore import QObject, QSettings, QProcess, QProcessEnvironment, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QPushButton

from legendary.models.game import LaunchParameters
from rare import shared
from rare.components.dialogs.uninstall_dialog import UninstallDialog
from rare.components.extra.console import ConsoleWindow
from rare.components.tabs.games import CloudSaveUtils
from rare.utils import legendary_utils

logger = getLogger("GameUtils")


class GameProcess(QProcess):
    game_finished = pyqtSignal(int, str)

    # noinspection PyUnresolvedReferences
    def __init__(self, app_name):
        super(GameProcess, self).__init__()
        self.app_name = app_name
        self.finished.connect(lambda x: self.game_finished.emit(x, self.app_name))


@dataclass
class RunningGameModel:
    process: GameProcess
    app_name: str
    always_ask_sync: bool = False


class GameUtils(QObject):
    running_games = dict()
    finished = pyqtSignal(str, str)  # app_name, error
    cloud_save_finished = pyqtSignal(str)
    launch_queue = dict()
    game_launched = pyqtSignal(str)
    update_list = pyqtSignal(str)

    def __init__(self, parent=None):
        super(GameUtils, self).__init__(parent=parent)

        self.core = shared.core
        self.console = ConsoleWindow()
        self.cloud_save_utils = CloudSaveUtils()
        self.cloud_save_utils.sync_finished.connect(self.sync_finished)

    def uninstall_game(self, app_name) -> bool:
        # returns if uninstalled
        game = self.core.get_game(app_name)
        igame = self.core.get_installed_game(app_name)
        if not os.path.exists(igame.install_path):
            if QMessageBox.Yes == QMessageBox.question(None, "Uninstall", self.tr(
                    "Game files of {} do not exist. Remove it from installed games?").format(igame.title),
                                                       QMessageBox.Yes | QMessageBox.No,
                                                       QMessageBox.Yes):
                self.core.lgd.remove_installed_game(app_name)
                return True
            else:
                return False

        infos = UninstallDialog(game).get_information()
        if infos == 0:
            return False
        legendary_utils.uninstall(game.app_name, self.core, infos)
        shared.signals.game_uninstalled.emit(app_name)
        return True

    def prepare_launch(self, app_name, offline: bool = False, skip_update_check: bool = False):
        game = self.core.get_game(app_name)
        dont_sync_after_finish = False

        if game.supports_cloud_saves:
            try:
                sync = self.cloud_save_utils.sync_before_launch_game(app_name)
            except ValueError:
                logger.info("Cancel startup")
                self.sync_finished(app_name)
            except AssertionError:
                dont_sync_after_finish = True
            else:
                if sync:
                    self.launch_queue[app_name] = (app_name, skip_update_check, offline)
                    return
            self.sync_finished(app_name)

        self.launch_game(app_name, offline, skip_update_check, ask_always_sync=dont_sync_after_finish)

    def launch_game(self, app_name: str, offline: bool = False, skip_update_check: bool = False, wine_bin: str = None,
                    wine_pfx: str = None, ask_always_sync: bool = False):
        if shared.args.offline:
            offline = True
        game = self.core.get_game(app_name)
        igame = self.core.get_installed_game(app_name)

        if not game:
            logger.error(f"{app_name} not found")
            self.finished.emit(app_name, self.tr("Game not found in available games"))
            return

        if QSettings().value("confirm_start", False, bool):
            if not QMessageBox.question(None, "Launch", self.tr("Do you want to launch {}").format(game.app_title),
                                        QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                logger.info("Cancel Startup")
                self.finished.emit(app_name, "")
                return
        logger.info("Launching " + game.app_title)

        if game.third_party_store == "Origin":
            offline = False
        else:
            if not igame:
                logger.error(f"{app_name} is not installed")
            if game.is_dlc:
                logger.error("Game is dlc")
                self.finished.emit(app_name, self.tr("Game is a DLC. Please launch base game instead"))
                return
            if not os.path.exists(igame.install_path):
                logger.error("Game doesn't exist")
                self.finished.emit(app_name,
                                   self.tr("Game files of {} do not exist. Please install game").format(game.app_title))
                return

        process = GameProcess(app_name)
        process.setProcessChannelMode(GameProcess.MergedChannels)

        if game.third_party_store != "Origin":
            if not offline:
                if not skip_update_check and not self.core.is_noupdate_game(app_name):
                    # check updates
                    try:
                        latest = self.core.get_asset(app_name, igame.platform, update=False)
                    except ValueError:
                        self.finished.emit(app_name, self.tr("Metadata doesn't exist"))
                        return
                    else:
                        if latest.build_version != igame.version:
                            self.finished.emit(app_name, self.tr("Please update game"))
                            return

            params: LaunchParameters = self.core.get_launch_parameters(app_name=app_name, offline=offline,
                                                                       wine_bin=wine_bin, wine_pfx=wine_pfx)

            full_params = list()
            full_params.extend(params.launch_command)
            full_params.append(os.path.join(params.game_directory, params.game_executable))
            full_params.extend(params.game_parameters)
            full_params.extend(params.egl_parameters)
            full_params.extend(params.user_parameters)

            process.setWorkingDirectory(params.working_directory)
            environment = QProcessEnvironment()
            full_env = os.environ.copy()
            full_env.update(params.environment)
            for env, value in full_env.items():
                environment.insert(env, value)

            if platform.system() != "Windows":
                # wine prefixes
                for env in ["STEAM_COMPAT_DATA_PATH", "WINEPREFIX"]:
                    if val := full_env.get(env):
                        if not os.path.exists(val):
                            try:
                                os.makedirs(val)
                            except PermissionError as e:
                                logger.error(str(e))
                                QMessageBox.warning(None, "Error",
                                                    self.tr(
                                                        "Error while launching {}. No permission to create {} for {}").format(
                                                        game.app_title, val, env))
                                process.deleteLater()
                                return
                # check wine executable
                if shutil.which(full_params[0]) is None:
                    # wine binary does not exist
                    QMessageBox.warning(None, "Warning", self.tr(
                        "Wine executable '{}' does not exist. Please change it in Settings").format(full_params[0]))
                    process.deleteLater()
                    return

            process.setProcessEnvironment(environment)
            process.game_finished.connect(self.game_finished)
            running_game = RunningGameModel(process=process, app_name=app_name, always_ask_sync=ask_always_sync)

            process.start(full_params[0], full_params[1:])
            self.game_launched.emit(app_name)
            logger.info(f"{game.app_title} launched")

            self.running_games[game.app_name] = running_game

        else:
            origin_uri = self.core.get_origin_uri(game.app_name, shared.args.offline)
            logger.info("Launch Origin Game: ")
            if platform.system() == "Windows":
                webbrowser.open(origin_uri)
                self.finished.emit(app_name, "")
                return
            wine_pfx = self.core.lgd.config.get(game.app_name, 'wine_prefix',
                                                fallback=os.path.expanduser("~/.wine"))
            if not wine_bin:
                wine_bin = self.core.lgd.config.get(game.app_name, 'wine_executable', fallback="/usr/bin/wine")

            if shutil.which(wine_bin) is None:
                # wine binary does not exist
                QMessageBox.warning(None, "Warning",
                                    self.tr("Wine executable '{}' does not exist. Please change it in Settings").format(
                                        wine_bin))
                process.deleteLater()
                return

            env = self.core.get_app_environment(game.app_name, wine_pfx=wine_pfx)

            if not env.get('WINEPREFIX') and not os.path.exists("/usr/bin/wine"):
                logger.error(f'In order to launch Origin correctly you must specify the wine binary and prefix '
                             f'to use in the configuration file or command line. See the README for details.')
                self.finished.emit(app_name, self.tr("No wine executable selected. Please set it in settings"))
                return

            environment = QProcessEnvironment()
            for e in env:
                environment.insert(e, env[e])
            process.setProcessEnvironment(environment)
            process.finished.connect(lambda x: self.game_finished(x, game.app_name))
            process.start(wine_bin, [origin_uri])

        if QSettings().value("show_console", False, bool):
            self.console.show()
            process.readyReadStandardOutput.connect(lambda: self.console.log(
                str(process.readAllStandardOutput().data(), "utf-8", "ignore")))
            process.readyReadStandardError.connect(lambda: self.console.error(
                str(process.readAllStandardError().data(), "utf-8", "ignore")))

    def game_finished(self, exit_code, app_name):
        logger.info("Game exited with exit code: " + str(exit_code))
        is_origin = self.core.get_game(app_name).third_party_store == "Origin"
        if exit_code == 53 and is_origin:
            msg_box = QMessageBox()
            msg_box.setText(self.tr("Origin is not installed. Do you want to download installer file? "))
            msg_box.addButton(QPushButton("Download"), QMessageBox.YesRole)
            msg_box.addButton(QPushButton("Cancel"), QMessageBox.RejectRole)
            resp = msg_box.exec()
            # click install button
            if resp == 0:
                webbrowser.open("https://www.dm.origin.com/download")
        if is_origin and exit_code == 1:
            QMessageBox.warning(None, "Warning",
                                self.tr("Failed to launch {}").format(self.core.get_game(app_name).app_title))

        game: RunningGameModel = self.running_games.get(app_name, None)
        if app_name in self.running_games.keys():
            self.running_games.pop(app_name)
        self.finished.emit(app_name, "")

        if QSettings().value("show_console", False, bool):
            self.console.log(f"Game exited with code: {exit_code}")

        if self.core.get_game(app_name).supports_cloud_saves:
            if exit_code != 0:
                r = QMessageBox.question(None, "Question", self.tr(
                    "Game exited with code {}, which is not a normal code. It could be caused by a crash. Do you want to sync cloud saves").format(
                    exit_code),
                                         buttons=QMessageBox.Yes | QMessageBox.No, defaultButton=QMessageBox.Yes)
                if r != QMessageBox.Yes:
                    return
            self.cloud_save_utils.game_finished(app_name, game.always_ask_sync)

    def sync_finished(self, app_name):
        if app_name in self.launch_queue.keys():
            self.cloud_save_finished.emit(app_name)
            params = self.launch_queue[app_name]
            self.launch_queue.pop(app_name)
            self.launch_game(*params)
        else:
            self.cloud_save_finished.emit(app_name)

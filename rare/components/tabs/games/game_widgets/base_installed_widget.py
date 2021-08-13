import os
import platform
from logging import getLogger

from PyQt5.QtCore import pyqtSignal, QProcess, QSettings, Qt, QByteArray
from PyQt5.QtWidgets import QGroupBox, QMessageBox, QAction

from custom_legendary.core import LegendaryCore
from custom_legendary.models.game import InstalledGame
from rare.components.dialogs.uninstall_dialog import UninstallDialog
from rare.components.extra.Console import ConsoleWindow
from rare.utils import legendary_utils
from rare.utils.utils import create_desktop_link

logger = getLogger("Game")


class BaseInstalledWidget(QGroupBox):
    launch_signal = pyqtSignal(str)
    show_info = pyqtSignal(str)
    finish_signal = pyqtSignal(str)
    update_list = pyqtSignal()
    proc: QProcess()

    def __init__(self, igame: InstalledGame, core: LegendaryCore, pixmap, offline):
        super(BaseInstalledWidget, self).__init__()
        self.igame = igame
        self.core = core
        self.game = self.core.get_game(self.igame.app_name)
        self.pixmap = pixmap
        self.game_running = False
        self.offline = offline
        self.update_available = self.core.get_asset(self.game.app_name, True).build_version != igame.version
        self.data = QByteArray()
        self.setContentsMargins(0, 0, 0, 0)
        self.settings = QSettings()

        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        launch = QAction(self.tr("Launch"), self)
        launch.triggered.connect(self.launch)
        self.addAction(launch)

        if os.path.exists(os.path.expanduser(f"~/Desktop/{self.igame.title}.desktop")) \
                or os.path.exists(os.path.expanduser(f"~/Desktop/{self.igame.title}.lnk")):
            self.create_desktop = QAction(self.tr("Remove Desktop link"))
        else:
            self.create_desktop = QAction(self.tr("Create Desktop link"))

        self.create_desktop.triggered.connect(lambda: self.create_desktop_link("desktop"))
        self.addAction(self.create_desktop)

        if platform.system() == "Linux":
            start_menu_file = os.path.expanduser(f"~/.local/share/applications/{self.igame.title}.desktop")
        elif platform.system() == "Windows":
            start_menu_file = os.path.expandvars("%appdata%/Microsoft/Windows/Start Menu")
        else:
            start_menu_file = ""
        if os.path.exists(start_menu_file):
            self.create_start_menu = QAction(self.tr("Remove start menu link"))
        else:
            self.create_start_menu = QAction(self.tr("Create start menu link"))

        self.create_start_menu.triggered.connect(lambda: self.create_desktop_link("start_menu"))
        self.addAction(self.create_start_menu)

        uninstall = QAction(self.tr("Uninstall"), self)
        uninstall.triggered.connect(self.uninstall)
        self.addAction(uninstall)

    def create_desktop_link(self, type_of_link):
        if platform.system() not in ["Windows", "Linux"]:
            QMessageBox.warning(self, "Warning",
                                f"Create a Desktop link is currently not supported on {platform.system()}")
            return
        if type_of_link == "desktop":
            path = os.path.expanduser(f"~/Desktop/")
        elif type_of_link == "start_menu":
            path = os.path.expanduser("~/.local/share/applications/")
        else:
            return
        if not (os.path.exists(os.path.expanduser(f"{path}{self.igame.title}.desktop"))
                or os.path.exists(os.path.expanduser(f"{path}{self.igame.title}.lnk"))):
            if not create_desktop_link(self.igame.app_name, self.core, type_of_link):
                return
            if type_of_link == "desktop":
                self.create_desktop.setText(self.tr("Remove Desktop link"))
            elif type_of_link == "start_menu":
                self.create_start_menu.setText(self.tr("Remove Start menu link"))
        else:
            if os.path.exists(os.path.expanduser(f"{path}{self.igame.title}.desktop")):
                os.remove(os.path.expanduser(f"{path}{self.igame.title}.desktop"))
            elif os.path.exists(os.path.expanduser(f"{path}{self.igame.title}.lnk")):
                os.remove(os.path.expanduser(f"{path}{self.igame.title}.lnk"))

            if type_of_link == "desktop":
                self.create_desktop.setText(self.tr("Create Desktop link"))
            elif type_of_link == "start_menu":
                self.create_start_menu.setText(self.tr("Create Start menu link"))

    def launch(self, offline=False, skip_version_check=False):
        if QSettings().value("confirm_start", False, bool):
            if not QMessageBox.question(self, "Launch", self.tr("Do you want to launch {}").format(self.game.app_title),
                                        QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                logger.info("Cancel Startup")
                return 1
        logger.info("Launching " + self.igame.title)
        if offline or self.offline:
            if not self.igame.can_run_offline:
                QMessageBox.warning(self, "Offline",
                                    self.tr("Game cannot run offline. Please start game in Online mode"))
                return

        try:
            self.proc, params = legendary_utils.launch_game(self.core, self.igame.app_name, offline,
                                                            skip_version_check=skip_version_check)
        except Exception as e:
            logger.error(e)
            QMessageBox.warning(self, "Error",
                                str(e))
            return

        if not self.proc:
            logger.error("Could not start process")
            return 1
        self.proc.finished.connect(self.finished)

        if self.settings.value("show_console", False, bool):
            self.console = ConsoleWindow()
            self.console.show()
            self.proc.readyReadStandardOutput.connect(lambda: self.console.log(
                bytes(self.proc.readAllStandardOutput()).decode("utf-8", errors="ignore")))
            self.proc.readyReadStandardError.connect(lambda: self.console.error(
                bytes(self.proc.readAllStandardOutput()).decode("utf-8", errors="ignore")))

        else:
            self.proc.readyReadStandardOutput.connect(self.stdout)
            self.proc.readyReadStandardError.connect(self.stderr)

        self.proc.start(params[0], params[1:])
        self.launch_signal.emit(self.igame.app_name)
        self.game_running = True

        return 0

    def stdout(self):
        data = self.proc.readAllStandardOutput()
        stdout = bytes(data).decode("utf-8", errors="ignore")
        print(stdout)

    def stderr(self):
        stderr = bytes(self.proc.readAllStandardError()).decode("utf-8", errors="ignore")
        print(stderr)
        # QMessageBox.warning(self, "Warning", stderr + "\nSee ~/.cache/rare/logs/")

    def finished(self, exit_code):
        logger.info("Game exited with exit code: " + str(exit_code))
        self.finish_signal.emit(self.game.app_name)
        self.game_running = False
        if self.settings.value("show_console", False, bool):
            self.console.log(f"Game exited with code: {exit_code}")

    def uninstall(self):
        infos = UninstallDialog(self.game).get_information()
        if infos == 0:
            print("Cancel Uninstall")
            return
        legendary_utils.uninstall(self.game.app_name, self.core, infos)
        self.update_list.emit(self.game.app_name)

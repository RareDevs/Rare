import json
import os
from logging import getLogger

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt5.QtWidgets import QDialog
from requests.exceptions import ConnectionError

from custom_legendary.core import LegendaryCore
from rare.components.dialogs.login import LoginDialog
from rare.ui.components.dialogs.launch_dialog import Ui_LaunchDialog
from rare.utils import steam_grades
from rare.utils.utils import download_images

logger = getLogger("Login")


class ImageThread(QThread):
    download_progess = pyqtSignal(int)

    def __init__(self, core: LegendaryCore, parent=None):
        super(ImageThread, self).__init__(parent)
        self.core = core

    def run(self):
        download_images(self.download_progess, self.core)
        self.download_progess.emit(100)


class SteamThread(QThread):
    progress = pyqtSignal(int)
    action = pyqtSignal(str)

    def __init__(self, core: LegendaryCore, parent):
        super(SteamThread, self).__init__(parent)
        self.core = core

    def run(self) -> None:
        gamelist = self.core.get_game_list(True)
        if not os.path.exists(os.path.expanduser("~/.cache/rare/game_list.json")):
            self.action.emit(self.tr("Getting data from ProtonDB"))
            steam_grades.upgrade_all([(i.app_title, i.app_name) for i in gamelist], self.progress)
        self.progress.emit(99)

        self.action.emit(self.tr("Checking Games for data"))
        grades = json.load(open(os.path.expanduser("~/.cache/rare/game_list.json")))
        ids = json.load(open(os.path.expanduser("~/.cache/rare/steam_ids.json")))
        for game in gamelist:
            if not grades.get(game.app_name):
                steam_id = steam_grades.get_steam_id(game.app_title, ids)
                grade = steam_grades.get_grade(steam_id)
                grades[game.app_name] = {
                    "steam_id": steam_id,
                    "grade": grade
                }
            if not grades[game.app_name].get("steam_id"):
                grades[game.app_name]["steam_id"] = steam_grades.get_steam_id(game.app_title)
            if not grades[game.app_name].get("grade"):
                grades[game.app_name]["grade"] = steam_grades.get_grade(game.app_title)

        with open(os.path.expanduser("~/.cache/rare/game_list.json"), "w") as f:
            f.write(json.dumps(grades))
            f.close()

        self.action.emit("Ready")
        self.progress.emit(100)


class LaunchDialog(QDialog, Ui_LaunchDialog):
    quit_app = pyqtSignal(int)
    start_app = pyqtSignal(bool)
    completed = False

    def __init__(self, core: LegendaryCore, offline=False, parent=None):
        super(LaunchDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.core = core
        self.offline = offline
        self.image_thread = None
        self.steam_thread = None
        if os.name == "nt":
            self.completed = True
            self.steam_info.setVisible(False)
            self.steam_prog_bar.setVisible(False)

    def login(self):
        do_launch = True
        try:
            if self.offline:
                pass
            else:
                if self.core.login():
                    logger.info("You are logged in")
                else:
                    raise ValueError("You are not logged in. Open Login Window")
        except ValueError as e:
            logger.info(str(e))
            do_launch = LoginDialog(core=self.core, parent=self).login()
        except ConnectionError as e:
            logger.warning(e)
            self.offline = True
        finally:
            if do_launch:
                self.show()
                self.launch()
            else:
                self.quit_app.emit(0)

    def launch(self):
        # self.core = core
        if not os.path.exists(p := os.path.expanduser("~/.cache/rare/images")):
            os.makedirs(p)

        if not self.offline:
            self.image_info.setText(self.tr("Downloading Images"))
            self.image_thread = ImageThread(self.core, self)
            self.image_thread.download_progess.connect(self.update_image_progbar)
            self.image_thread.finished.connect(self.finish)
            self.image_thread.finished.connect(lambda: self.image_info.setText(self.tr("Ready")))
            self.image_thread.finished.connect(self.image_thread.quit)
            self.image_thread.finished.connect(self.image_thread.deleteLater)
            self.image_thread.start()
            # not disabled and not windows
            if (not QSettings().value("disable_protondb", False, bool)) and (not os.name == "nt"):
                self.steam_thread = SteamThread(self.core, self)
                self.steam_thread.progress.connect(self.update_steam_prog_bar)
                self.steam_thread.action.connect(lambda x: self.steam_info.setText(x))
                self.steam_thread.finished.connect(self.finish)
                self.steam_thread.finished.connect(lambda: self.steam_info.setText(self.tr("Ready")))
                self.steam_thread.finished.connect(self.steam_thread.quit)
                self.steam_thread.finished.connect(self.steam_thread.deleteLater)
                self.steam_thread.start()
            else:
                self.completed = True
                self.steam_info.setVisible(False)
                self.steam_prog_bar.setVisible(False)

    def update_steam_prog_bar(self, value):
        self.steam_prog_bar.setValue(value)

    def update_image_progbar(self, i: int):
        self.image_prog_bar.setValue(i)

    def finish(self):
        if self.completed:
            self.image_info.setText(self.tr("Starting..."))
            self.image_prog_bar.setValue(100)
            self.steam_prog_bar.setValue(100)
            self.start_app.emit(self.offline)
        else:
            self.completed = True

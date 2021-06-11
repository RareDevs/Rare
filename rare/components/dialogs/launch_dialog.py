import json
import os
from logging import getLogger

from PyQt5.QtCore import QThread, pyqtSignal, QSettings, Qt
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


class LoginThread(QThread):
    login = pyqtSignal()
    start_app = pyqtSignal(bool)  # offline

    def __init__(self, core: LegendaryCore):
        super(LoginThread, self).__init__()
        self.core = core

    def run(self):
        logger.info("Try if you are logged in")
        try:
            if self.core.login():
                logger.info("You are logged in")
                self.start_app.emit(False)
            else:
                self.run()
        except ValueError:
            logger.info("You are not logged in. Open Login Window")
            self.login.emit()
        except ConnectionError as e:
            logger.warning(e)
            self.start_app.emit(True)


class LaunchDialog(QDialog, Ui_LaunchDialog):
    start_app = pyqtSignal(bool)
    finished = False

    def __init__(self, core: LegendaryCore, offline):
        super(LaunchDialog, self).__init__()
        self.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        if os.name == "nt":
            self.finished = True
            self.steam_info.setVisible(False)
            self.steam_prog_bar.setVisible(False)
        self.core = core
        if not offline:
            self.login_thread = LoginThread(core)
            self.login_thread.login.connect(self.login)
            self.login_thread.start_app.connect(self.launch)
            self.login_thread.start()

        else:
            self.launch(offline)

    def login(self):
        self.hide()
        if LoginDialog(core=self.core).login():
            self.show()
            self.login_thread.start()
        else:
            exit(0)

    def launch(self, offline=False):
        # self.core = core
        if not os.path.exists(p := os.path.expanduser("~/.cache/rare/images")):
            os.makedirs(p)
        self.offline = offline

        if not offline:

            self.image_info.setText(self.tr("Downloading Images"))
            self.img_thread = ImageThread(self.core, self)
            self.img_thread.download_progess.connect(self.update_image_progbar)
            self.img_thread.finished.connect(self.finish)
            self.img_thread.start()
            # not disabled and not windows
            if (not QSettings().value("disable_protondb", False, bool)) and (not os.name == "nt"):
                self.steam_thread = SteamThread(self.core, self)
                self.steam_thread.progress.connect(self.update_steam_prog_bar)
                self.steam_thread.action.connect(lambda x: self.steam_info.setText(x))
                self.steam_thread.finished.connect(self.finish)
                self.steam_thread.start()
            else:
                self.finished = True
                self.steam_info.setVisible(False)
                self.steam_prog_bar.setVisible(False)

        else:
            self.finished = True
            self.finish()

    def update_steam_prog_bar(self, value):
        self.steam_prog_bar.setValue(value)

    def update_image_progbar(self, i: int):
        self.image_prog_bar.setValue(i)

    def finish(self):
        if self.finished:
            self.image_info.setText(self.tr("Starting..."))
            self.image_prog_bar.setValue(100)
            self.steam_prog_bar.setValue(100)
            self.start_app.emit(self.offline)
        else:
            self.finished = True

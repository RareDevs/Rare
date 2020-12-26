import time
from logging import getLogger

from PyQt5.QtCore import QThread, QProcess
from PyQt5.QtWidgets import QVBoxLayout, QProgressBar, QPushButton, QLabel, QWidget, QHBoxLayout

from legendary.core import LegendaryCore
from legendary.models.game import InstalledGame
from multiprocessing import Queue as MPQueue
logger = getLogger("Updates")


class UpdateThread(QThread):
    def __init__(self, dlm):
        super(UpdateThread, self).__init__()
        self.dlm = dlm
        logging_queue = MPQueue(-1)
        self.dlm.logging_queue = logging_queue

    def run(self):
        self.dlm.start()
        self.dlm.join()


class UpdateProc(QProcess):
    def __init__(self):
        super(UpdateProc, self).__init__()


class UpdateWidget(QWidget):

    def __init__(self, game: InstalledGame, core: LegendaryCore):
        super(UpdateWidget, self).__init__()
        self.updating = False
        self.game = game
        self.core = core
        self.layout = QVBoxLayout()
        self.childlayout = QHBoxLayout()
        self.label = QLabel("Update available for " + self.game.title)
        self.button = QPushButton("Update")
        self.button.clicked.connect(self.update_game)

        self.childlayout.addWidget(self.label)
        self.childlayout.addWidget(self.button)
        self.layout.addLayout(self.childlayout)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.layout.addWidget(self.progress_bar)

        self.setLayout(self.layout)

    def update_game2(self):
        if not self.updating:
            logger.info("Update " + self.game.title)
            game = self.core.get_game(self.game.app_name)
            logger.info("Prepare Download")
            dlm, analysis, manifest = self.core.prepare_download(game=game, base_game=game)

            if not analysis.dl_size:
                logger.info("Game is up to date, sorry")

            logger.info(f"Install size: {round(analysis.install_size / (1024 ** 3),2)} GB")
            logger.info(f"Download size: {round(analysis.dl_size/(1024**3), 2)} GB")
            installed_game = self.core.get_installed_game(self.game.app_name)
            res = self.core.check_installation_conditions(analysis, installed_game, self.core.get_game(self.game.app_name), True)
            if res.failures:
                logger.error("Fail")
            if res.warnings:
                for warn in sorted(res.warnings):
                    logger.warning(warn)
            start_time = time.time()
            self.update_thread = UpdateThread(dlm)
            self.update_thread.finished.connect(self.finished)
            self.update_thread.start()
            self.button.setDisabled(True)
            # TODO Wird 1000% nicht funktionieren

        else:
            logger.info("Terminate process")
            self.thread.kill()
            self.button.setText("Update")
            self.updating = False

    def update_game(self):
        self.proc = QProcess()
        self.proc.start("legendary", ["-y", "update", self.game.app_name])

    def finished(self):
        self.setVisible(False)

    def start(self):
        self.button.setText("Cancel")
        self.updating = True

    def get_update_info(self):
        shit, infos, game = self.core.prepare_download(self.core.get_game(self.game.app_name),
                                                       self.core.get_game(self.game.app_name))

    def dataReady(self):
        bytes = self.thread.readAllStandardOutput()
        byte_list = bytes.split('\n')
        data = []
        for i in byte_list:
            data.append(byte_list)

        text = data[0].decode()

        print(data)


class UpdateTab(QWidget):

    def __init__(self, parent, core: LegendaryCore):
        super(UpdateTab, self).__init__(parent=parent)
        self.core = core
        self.layout = QVBoxLayout()
        update_games = self.get_updates()

        if update_games:
            for game in self.get_updates():
                self.layout.addWidget(UpdateWidget(game, core))
        else:
            self.layout.addWidget(QLabel("No updates available"))
        self.layout.addStretch(1)
        self.setLayout(self.layout)

    def get_updates(self):
        self.core.get_assets(True)
        update_games = []
        games=sorted(self.core.get_installed_list(), key=lambda x: x.title)
        versions={}
        for game in games:
            try:
                versions[game.app_name] = self.core.get_asset(game.app_name).build_version
            except:
                logger.error(f"Metadata for {game.title} is missing")

            if versions[game.app_name] != game.version:
                update_games.append(game)
        return update_games

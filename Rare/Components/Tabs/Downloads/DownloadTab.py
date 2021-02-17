import os
import subprocess
import time
from logging import getLogger

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QWidget, QMessageBox, QVBoxLayout, QLabel, QGridLayout, QProgressBar
from legendary.core import LegendaryCore

from Rare.utils.Dialogs.InstallDialog import InstallInfoDialog

logger = getLogger("Download")


class DownloadThread(QThread):
    status = pyqtSignal(str)

    def __init__(self, dlm, core: LegendaryCore, igame):
        super(DownloadThread, self).__init__()
        self.dlm = dlm
        self.core = core
        self.igame = igame

    def run(self):
        start_time = time.time()
        try:

            self.dlm.start()
            self.dlm.join()
        except:
            logger.error(f"Installation failed after{time.time() - start_time:.02f} seconds.")
            self.status.emit("error")
            return

        else:
            self.status.emit("dl_finished")
            end_t = time.time()
            game = self.core.get_game(self.igame.app_name)
            postinstall = self.core.install_game(self.igame)
            if postinstall:
                self._handle_postinstall(postinstall, self.igame)
            dlcs = self.core.get_dlc_for_game(self.igame.app_name)
            if dlcs:
                print('The following DLCs are available for this game:')
                for dlc in dlcs:
                    print(f' - {dlc.app_title} (App name: {dlc.app_name}, version: {dlc.app_version})')
                print('Manually installing DLCs works the same; just use the DLC app name instead.')

                # install_dlcs = QMessageBox.question(self, "", "Do you want to install the prequisites", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes
                # TODO
            if game.supports_cloud_saves and not game.is_dlc:
                logger.info('This game supports cloud saves, syncing is handled by the "sync-saves" command.')
                logger.info(f'To download saves for this game run "legendary sync-saves {game.app_name}"')

        self.status.emit("finish")

    def _handle_postinstall(self, postinstall, igame):
        print('This game lists the following prequisites to be installed:')
        print(f'- {postinstall["name"]}: {" ".join((postinstall["path"], postinstall["args"]))}')
        if os.name == 'nt':
            if QMessageBox.question(self, "", "Do you want to install the prequisites",
                                    QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                self.core.prereq_installed(igame.app_name)
                req_path, req_exec = os.path.split(postinstall['path'])
                work_dir = os.path.join(igame.install_path, req_path)
                fullpath = os.path.join(work_dir, req_exec)
                subprocess.call([fullpath, postinstall['args']], cwd=work_dir)
            else:
                self.core.prereq_installed(self.igame.app_name)

        else:
            logger.info('Automatic installation not available on Linux.')


class DownloadTab(QWidget):
    finished = pyqtSignal()
    thread: QThread

    def __init__(self, core: LegendaryCore):
        super(DownloadTab, self).__init__()
        self.core = core
        self.layout = QVBoxLayout()

        self.installing_game = QLabel("Installing Game: None")
        self.dl_speed = QLabel("Download speed: 0MB/s")
        self.cache_used = QLabel("Cache used: 0MB")
        self.downloaded = QLabel("Downloaded: 0MB")

        self.info_layout = QGridLayout()

        self.info_layout.addWidget(self.installing_game, 0, 0)
        self.info_layout.addWidget(self.dl_speed, 0, 1)
        self.info_layout.addWidget(self.cache_used, 1,0)
        self.info_layout.addWidget(self.downloaded, 1,1)

        self.layout.addLayout(self.info_layout)
        self.prog_bar = QProgressBar()
        self.layout.addWidget(self.prog_bar)

        self.layout.addWidget(QLabel("WARNING: This feature is not implemented. It  is normal, if there is no progress. The progress is in console"))

        self.installing_game_widget = QLabel("No active Download")
        self.layout.addWidget(self.installing_game_widget)

        self.layout.addStretch(1)

        self.setLayout(self.layout)

    def install_game(self, options: {}):
        game = self.core.get_game(options["app_name"])
        dlm, analysis, igame = self.core.prepare_download(
            game=game,
            base_path=options["options"]["path"],
            max_workers=options["options"]["max_workers"])
        if not analysis.dl_size:
            QMessageBox.information(self, "Warning", "Download size is 0")
            return
        # Information
        if not InstallInfoDialog(dl_size=analysis.dl_size, install_size=analysis.install_size).get_accept():
            return

        self.installing_game_widget.setText("")
        self.installing_game.setText("Installing Game: "+ game.app_title)
        res = self.core.check_installation_conditions(analysis=analysis, install=igame, game=game,
                                                      updating=self.core.is_installed(options["app_name"]),
                                                      )
        if res.warnings:
            for w in sorted(res.warnings):
                logger.warning(w)
        if res.failures:
            for msg in sorted(res.failures):
                logger.error(msg)
            logger.error('Installation cannot proceed, exiting.')
            QMessageBox.warning(self, "Installation failed", "Installation failed. See logs for more information")
            return

        self.thread = DownloadThread(dlm, self.core, igame)
        self.thread.status.connect(self.status)
        self.thread.start()

    def status(self, text):
        if text == "dl_finished":
            pass
        elif text == "finish":
            QMessageBox.information(self, "Info", "Download finished")
            self.finished.emit()
            self.installing_game.setText("Installing Game: No running download")
        elif text == "error":
            QMessageBox.warning(self, "warn", "Download error")

    def update_game(self, app_name: str):
        print("Update ", app_name)

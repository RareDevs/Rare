import os
import subprocess
import time
from logging import getLogger

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QWidget, QMessageBox, QVBoxLayout, QLabel, QGridLayout, QProgressBar, QPushButton
from legendary.core import LegendaryCore
from legendary.models.game import Game
from notifypy import Notify

from Rare.Components.Dialogs.InstallDialog import InstallInfoDialog
from Rare.utils.LegendaryApi import VerifyThread
from Rare.utils.Models import InstallOptions

logger = getLogger("Download")


class DownloadThread(QThread):
    status = pyqtSignal(str)

    def __init__(self, dlm, core: LegendaryCore, igame, repair=False, repair_file=None):
        super(DownloadThread, self).__init__()
        self.dlm = dlm
        self.core = core
        self.igame = igame
        self.repair = repair
        self.repair_file = repair_file

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
        old_igame = self.core.get_installed_game(game.app_name)
        if old_igame and self.repair and os.path.exists(self.repair_file):
            if old_igame.needs_verification:
                old_igame.needs_verification = False
                self.core.install_game(old_igame)

            logger.debug('Removing repair file.')
            os.remove(self.repair_file)
        if old_igame and old_igame.install_tags != self.igame.install_tags:
            old_igame.install_tags = self.igame.install_tags
            self.logger.info('Deleting now untagged files.')
            self.core.uninstall_tag(old_igame)
            self.core.install_game(old_igame)

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

    def __init__(self, core: LegendaryCore, updates: list):
        super(DownloadTab, self).__init__()
        self.core = core
        self.layout = QVBoxLayout()
        self.active_game: Game = None

        self.installing_game = QLabel(self.tr("No active Download"))
        self.dl_speed = QLabel(self.tr("Download speed") + ": 0MB/s")
        self.cache_used = QLabel(self.tr("Cache used") + ": 0MB")
        self.downloaded = QLabel(self.tr("Downloaded") + ": 0MB")

        self.info_layout = QGridLayout()

        self.info_layout.addWidget(self.installing_game, 0, 0)
        self.info_layout.addWidget(self.dl_speed, 0, 1)
        self.info_layout.addWidget(self.cache_used, 1, 0)
        self.info_layout.addWidget(self.downloaded, 1, 1)

        self.layout.addLayout(self.info_layout)
        self.prog_bar = QProgressBar()
        self.layout.addWidget(self.prog_bar)
        label = QLabel(
            self.tr("<b>WARNING</b>: The progress bar is not implemented. It  is normal, if there is no progress. The "
                    "progress is visible in console, because Legendary prints output to console. A pull request is "
                    "active to get output"))
        label.setWordWrap(True)
        self.layout.addWidget(label)

        self.installing_game_widget = QLabel(self.tr("No active Download"))
        self.layout.addWidget(self.installing_game_widget)

        self.update_title = QLabel(f"<h2>{self.tr('Updates')}</h2>")
        self.update_title.setStyleSheet("""
            QLabel{
                margin-top: 20px;
            }
        """)
        self.layout.addWidget(self.update_title)
        if not updates:
            self.update_text = QLabel(self.tr("No updates available"))
            self.layout.addWidget(self.update_text)
        else:
            for i in updates:
                widget = UpdateWidget(core, i)
                self.layout.addWidget(widget)
                widget.update.connect(self.update_game)

        self.layout.addStretch(1)

        self.setLayout(self.layout)

    def install_game(self, options: InstallOptions):
        game = self.core.get_game(options.app_name, update_meta=True)
        if self.core.is_installed(options.app_name):
            igame = self.core.get_installed_game(options.app_name)
            if igame.needs_verification and not options.repair:
                options.repair = True
        repair_file = None
        if options.repair:
            repair_file = os.path.join(self.core.lgd.get_tmp_path(), f'{options.app_name}.repair')

        if not game:
            QMessageBox.warning(self, "Error", self.tr("Could not find Game in your library"))
            return

        if game.is_dlc:
            logger.info("DLCs are currently not supported")
            return

        if game.is_dlc:
            logger.info('Install candidate is DLC')
            app_name = game.metadata['mainGameItem']['releaseInfo'][0]['appId']
            base_game = self.core.get_game(app_name)
            # check if base_game is actually installed
            if not self.core.is_installed(app_name):
                # download mode doesn't care about whether or not something's installed
                logger.error("Base Game is not installed")
                return
        else:
            base_game = None

        if options.repair:
            repair_file = os.path.join(self.core.lgd.get_tmp_path(), f'{options.app_name}.repair')
            if not self.core.is_installed(game.app_name):
                return

            if not os.path.exists(repair_file):
                logger.info("Game has not been verified yet")
                if QMessageBox.question(self, "Verify", self.tr("Game has not been verified yet. Do you want to verify first?"),
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
                    self.verify_thread = VerifyThread(self.core, game.app_name)
                    self.verify_thread.finished.connect(
                        lambda: self.prepare_download(game, options, base_game, repair_file))
                    self.verify_thread.start()
                return
        self.prepare_download(game, options, base_game, repair_file)

    def prepare_download(self, game, options, base_game, repair_file):
        dlm, analysis, igame = self.core.prepare_download(
            game=game,
            base_path=options.path,
            max_workers=options.max_workers, base_game=base_game, repair=options.repair)
        if not analysis.dl_size:
            QMessageBox.information(self, "Warning", self.tr("Download size is 0. Game already exists"))
            return
        # Information
        if not InstallInfoDialog(dl_size=analysis.dl_size, install_size=analysis.install_size).get_accept():
            return

        self.installing_game_widget.setText("")
        self.installing_game.setText(self.tr("Installing Game: ") + game.app_title)
        res = self.core.check_installation_conditions(analysis=analysis, install=igame, game=game,
                                                      updating=self.core.is_installed(options.app_name),
                                                      )
        if res.warnings:
            for w in sorted(res.warnings):
                logger.warning(w)
        if res.failures:
            for msg in sorted(res.failures):
                logger.error(msg)
            logger.error('Installation cannot proceed, exiting.')
            QMessageBox.warning(self, "Installation failed",
                                self.tr("Installation failed. See logs for more information"))
            return
        self.active_game = game
        self.thread = DownloadThread(dlm, self.core, igame, options.repair, repair_file)
        self.thread.status.connect(self.status)
        self.thread.start()

    def status(self, text):
        if text == "dl_finished":
            pass
        elif text == "finish":
            notification = Notify()
            notification.title = self.tr("Installation finished")
            notification.message = self.tr("Download of game ") + self.active_game.app_title
            notification.send()
            # QMessageBox.information(self, "Info", "Download finished")
            self.finished.emit()
            self.installing_game.setText(self.tr("Installing Game: No active download"))
        elif text == "error":
            QMessageBox.warning(self, "warn", "Download error")

    def update_game(self, app_name: str):
        print("Update ", app_name)
        self.install_game(InstallOptions(app_name))

    def repair(self):
        pass


class UpdateWidget(QWidget):
    update = pyqtSignal(str)

    def __init__(self, core: LegendaryCore, app_name):
        super(UpdateWidget, self).__init__()
        self.core = core
        self.game = core.get_installed_game(app_name)

        self.layout = QVBoxLayout()
        self.title = QLabel(self.game.title)
        self.layout.addWidget(self.title)

        self.update_button = QPushButton(self.tr("Update Game"))
        self.update_button.clicked.connect(lambda: self.update.emit(app_name))
        self.layout.addWidget(self.update_button)

        self.setLayout(self.layout)

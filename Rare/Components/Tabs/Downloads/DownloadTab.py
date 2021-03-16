import os
import queue
import subprocess
import time
from logging import getLogger
from multiprocessing import Queue as MPQueue

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QMessageBox, QVBoxLayout, QLabel, QGridLayout, QProgressBar, QPushButton, QDialog, \
    QListWidget, QHBoxLayout



from custom_legendary.core import LegendaryCore
from custom_legendary.downloader.manager import DLManager
from custom_legendary.models.downloading import UIUpdate
from custom_legendary.models.game import Game
from custom_legendary.utils.selective_dl import games

from Rare.Components.Dialogs.InstallDialog import InstallInfoDialog
from Rare.utils.Models import InstallOptions, KillDownloadException

logger = getLogger("Download")


class DownloadThread(QThread):
    status = pyqtSignal(str)
    statistics = pyqtSignal(UIUpdate)
    kill = False

    def __init__(self, dlm: DLManager, core: LegendaryCore, status_queue: MPQueue, igame, repair=False,
                 repair_file=None):
        super(DownloadThread, self).__init__()
        self.dlm = dlm
        self.core = core
        self.status_queue = status_queue
        self.igame = igame
        self.repair = repair
        self.repair_file = repair_file

    def run(self):
        start_time = time.time()
        try:

            self.dlm.start()
            time.sleep(1)
            while self.dlm.is_alive():
                if self.kill:
                    #raise KillDownloadException()
                    # TODO kill download queue, workers
                    pass
                try:
                    self.statistics.emit(self.status_queue.get(timeout=1))
                except queue.Empty:
                    pass

            self.dlm.join()

        except KillDownloadException:
            self.status.emit("stop")
            logger.info("Downlaod can be continued later")
            self.dlm.kill()
            return

        except Exception as e:
            logger.error(f"Installation failed after {time.time() - start_time:.02f} seconds: {e}")
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
        self.dl_speed = QLabel()
        self.cache_used = QLabel()
        self.downloaded = QLabel()

        self.info_layout = QGridLayout()

        self.info_layout.addWidget(self.installing_game, 0, 0)
        self.info_layout.addWidget(self.dl_speed, 0, 1)
        self.info_layout.addWidget(self.cache_used, 1, 0)
        self.info_layout.addWidget(self.downloaded, 1, 1)
        self.layout.addLayout(self.info_layout)

        self.mini_layout = QHBoxLayout()

        self.prog_bar = QProgressBar()
        self.prog_bar.setMaximum(100)
        self.mini_layout.addWidget(self.prog_bar)

        self.kill_button = QPushButton(self.tr("Stop Download"))
        # self.mini_layout.addWidget(self.kill_button)
        self.kill_button.setDisabled(True)
        self.kill_button.clicked.connect(self.stop_download)

        self.layout.addLayout(self.mini_layout)

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

    def stop_download(self):
        self.thread.kill = True

    def install_game(self, options: InstallOptions):
        game = self.core.get_game(options.app_name, update_meta=True)
        status_queue = MPQueue()
        try:
            dlm, analysis, game, igame, repair, repair_file = self.core.prepare_download(
                app_name=options.app_name,
                base_path=options.path,
                force=False,  # TODO allow overwrite
                no_install=options.download_only,
                status_q=status_queue,
                # max_shm=,
                max_workers=options.max_workers,
                # game_folder=,
                # disable_patching=,
                # override_manifest=,
                # override_old_manifest=,
                # override_base_url=,
                # platform_override=,
                # file_prefix_filter=,
                # file_exclude_filter=,
                # file_install_tag=,
                # dl_optimizations=,
                # dl_timeout=,
                repair=options.repair,
                # repair_use_latest=,
                # ignore_space_req=,
                # disable_delta=,
                # override_delta_manifest=,
                # reset_sdl=,
                sdl_prompt=self.sdl_prompt)
        except Exception as e:
            QMessageBox.warning(self, self.tr("Error preparing download"),
                                str(e))
            return

        if not analysis.dl_size:
            QMessageBox.information(self, "Warning", self.tr("Download size is 0. Game already exists"))
            return
        # Information
        if not InstallInfoDialog(dl_size=analysis.dl_size, install_size=analysis.install_size).get_accept():
            return

        self.active_game = game
        self.thread = DownloadThread(dlm, self.core, status_queue, igame, options.repair, repair_file)
        self.thread.status.connect(self.status)
        self.thread.statistics.connect(self.statistics)
        self.thread.start()
        self.kill_button.setDisabled(False)
        self.installing_game.setText("Installing Game: " + self.active_game.app_title)

    def sdl_prompt(self, app_name: str = '', title: str = '') -> list:
        sdl = QDialog()
        sdl.setWindowTitle('Select Additional Downloads')

        layout = QVBoxLayout(sdl)
        sdl.setLayout(layout)

        pack_list = QListWidget()
        layout.addWidget(pack_list)

        done = QPushButton(text='Done')
        done.clicked.connect(sdl.accept)
        layout.addWidget(done)

        tags = ['']
        if '__required' in games[app_name]:
            tags.extend(games[app_name]['__required']['tags'])

        # add available additional downloads to list
        pack_list.addItems([tag + ': ' + info['name'] for tag, info in games[app_name].items() if tag != '__required'])

        # enable checkboxes
        for i in range(len(pack_list)):
            item = pack_list.item(i)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Unchecked)

        sdl.exec_()

        # read checkboxes states
        for i in range(len(pack_list)):
            item = pack_list.item(i)
            if item.checkState() == Qt.Checked:
                tag = item.text().split(':')[0]
                tags.extend(games[app_name][tag]['tags'])

        return tags

    def status(self, text):
        if text == "dl_finished":
            pass
        elif text == "finish":
            try:
                from notifypy import Notify
            except ModuleNotFoundError:
                logger.warning("No Notification Module found")
            else:
                notification = Notify()
                notification.title = self.tr("Installation finished")
                notification.message = self.tr("Download of game ") + self.active_game.app_title
                notification.send()
            # QMessageBox.information(self, "Info", "Download finished")
            self.finished.emit()
            self.installing_game.setText(self.tr("Installing Game: No active download"))
            self.prog_bar.setValue(0)
            self.dl_speed.setText("")
            self.cache_used.setText("")
            self.downloaded.setText("")
        elif text == "error":
            QMessageBox.warning(self, "warn", "Download error")

        elif text == "stop":
            self.kill_button.setDisabled(True)
            self.installing_game.setText(self.tr("Installing Game: No active download"))
            self.prog_bar.setValue(0)
            self.dl_speed.setText("")
            self.cache_used.setText("")
            self.downloaded.setText("")

    def statistics(self, ui_update: UIUpdate):
        self.prog_bar.setValue(ui_update.progress)
        self.dl_speed.setText(self.tr("Download speed") + f": {ui_update.download_speed / 1024 / 1024:.02f}MB/s")
        self.cache_used.setText(self.tr("Cache used") + f": {ui_update.cache_usage / 1024 / 1024:.02f}MB")
        self.downloaded.setText(self.tr("Downloaded") + f": {ui_update.total_downloaded / 1024 / 1024:.02f}MB")

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

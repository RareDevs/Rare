import os
import queue
import subprocess
import time
from logging import getLogger
from multiprocessing import Queue as MPQueue

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox

from rare.utils.models import KillDownloadException

from custom_legendary.core import LegendaryCore
from custom_legendary.downloader.manager import DLManager
from custom_legendary.models.downloading import UIUpdate

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
                    # raise KillDownloadException()
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


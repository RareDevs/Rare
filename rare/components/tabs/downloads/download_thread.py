import os
import platform
import queue
import subprocess
import sys
import time
from logging import getLogger
from queue import Empty

import psutil
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox

from legendary.core import LegendaryCore
from legendary.models.downloading import UIUpdate, WriterTask
from rare.utils.models import InstallQueueItemModel

logger = getLogger("Download")


class DownloadThread(QThread):
    status = pyqtSignal(str)
    statistics = pyqtSignal(UIUpdate)

    def __init__(self, core: LegendaryCore, queue_item: InstallQueueItemModel):
        super(DownloadThread, self).__init__()
        self.core = core
        self.dlm = queue_item.download.dlmanager
        self.no_install = queue_item.options.no_install
        self.status_q = queue_item.status_q
        self.igame = queue_item.download.igame
        self.repair = queue_item.download.repair
        self.repair_file = queue_item.download.repair_file
        self._kill = False

    def run(self):
        start_time = time.time()
        dl_stopped = False
        try:

            self.dlm.start()
            time.sleep(1)
            while self.dlm.is_alive():
                if self._kill:
                    self.status.emit("stop")
                    logger.info("Download stopping...")

                    # The code below is a temporary solution.
                    # It should be removed once legendary supports stopping downloads more gracefully.

                    self.dlm.running = False

                    # send conditions to unlock threads if they aren't already
                    for cond in self.dlm.conditions:
                        with cond:
                            cond.notify()

                    # make sure threads are dead.
                    for t in self.dlm.threads:
                        t.join(timeout=5.0)
                        if t.is_alive():
                            logger.warning(f'Thread did not terminate! {repr(t)}')

                    # clean up all the queues, otherwise this process won't terminate properly
                    for name, q in zip(('Download jobs', 'Writer jobs', 'Download results', 'Writer results'),
                                       (self.dlm.dl_worker_queue, self.dlm.writer_queue, self.dlm.dl_result_q,
                                        self.dlm.writer_result_q)):
                        logger.debug(f'Cleaning up queue "{name}"')
                        try:
                            while True:
                                _ = q.get_nowait()
                        except Empty:
                            q.close()
                            q.join_thread()
                        except AttributeError:
                            logger.warning(f'Queue {name} did not close')

                    if self.dlm.writer_queue:
                        # cancel installation
                        self.dlm.writer_queue.put_nowait(WriterTask('', kill=True))

                    # forcibly kill DL workers that are not actually dead yet
                    for child in self.dlm.children:
                        if child.exitcode is None:
                            child.terminate()

                    if self.dlm.shared_memory:
                        # close up shared memory
                        self.dlm.shared_memory.close()
                        self.dlm.shared_memory.unlink()
                        self.dlm.shared_memory = None

                    self.dlm.kill()

                    # force kill any threads that are somehow still alive
                    for proc in psutil.process_iter():
                        # check whether the process name matches
                        if sys.platform in ['linux', 'darwin'] and proc.name() == 'DownloadThread':
                            proc.kill()
                        elif sys.platform == 'win32' and proc.name() == 'python.exe' and proc.create_time() >= start_time:
                            proc.kill()

                    logger.info("Download stopped. It can be continued later.")
                    dl_stopped = True
                try:
                    if not dl_stopped:
                        self.statistics.emit(self.status_q.get(timeout=1))
                except queue.Empty:
                    pass

            self.dlm.join()

        except Exception as e:
            logger.error(f"Installation failed after {time.time() - start_time:.02f} seconds: {e}")
            self.status.emit("error " + str(e))
            return

        else:
            if dl_stopped:
                return
            self.status.emit("dl_finished")
            end_t = time.time()
            logger.info(f"Download finished in {start_time - end_t}s")
            game = self.core.get_game(self.igame.app_name)

            if not self.no_install:
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
        if platform.system() == "Windows":
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

    def kill(self):
        self._kill = True

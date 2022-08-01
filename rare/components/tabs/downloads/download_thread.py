import os
import platform
import queue
import sys
import time
from logging import getLogger
from queue import Empty

import psutil
from PyQt5.QtCore import QThread, pyqtSignal, QProcess
from legendary.core import LegendaryCore
from legendary.models.downloading import WriterTask

from rare.shared import GlobalSignalsSingleton, LegendaryCLISingleton
from rare.models.install import InstallQueueItemModel
from rare.utils.misc import create_desktop_link
from rare.lgndr.downloading import UIUpdate

logger = getLogger("DownloadThread")


class DownloadThread(QThread):
    status = pyqtSignal(str)
    statistics = pyqtSignal(UIUpdate)

    def __init__(self, core: LegendaryCore, item: InstallQueueItemModel):
        super(DownloadThread, self).__init__()
        self.signals = GlobalSignalsSingleton()
        self.core: LegendaryCore = core
        self.item: InstallQueueItemModel = item

        self._kill = False

    def run(self):
        start_time = time.time()
        dl_stopped = False
        try:

            self.item.download.dlmanager.start()
            time.sleep(1)
            while self.item.download.dlmanager.is_alive():
                if self._kill:
                    self.status.emit("stop")
                    logger.info("Download stopping...")

                    # The code below is a temporary solution.
                    # It should be removed once legendary supports stopping downloads more gracefully.

                    self.item.download.dlmanager.running = False

                    # send conditions to unlock threads if they aren't already
                    for cond in self.item.download.dlmanager.conditions:
                        with cond:
                            cond.notify()

                    # make sure threads are dead.
                    for t in self.item.download.dlmanager.threads:
                        t.join(timeout=5.0)
                        if t.is_alive():
                            logger.warning(f"Thread did not terminate! {repr(t)}")

                    # clean up all the queues, otherwise this process won't terminate properly
                    for name, q in zip(
                            (
                                    "Download jobs",
                                    "Writer jobs",
                                    "Download results",
                                    "Writer results",
                            ),
                            (
                                    self.item.download.dlmanager.dl_worker_queue,
                                    self.item.download.dlmanager.writer_queue,
                                    self.item.download.dlmanager.dl_result_q,
                                    self.item.download.dlmanager.writer_result_q,
                            ),
                    ):
                        logger.debug(f'Cleaning up queue "{name}"')
                        try:
                            while True:
                                _ = q.get_nowait()
                        except Empty:
                            q.close()
                            q.join_thread()
                        except AttributeError:
                            logger.warning(f"Queue {name} did not close")

                    if self.item.download.dlmanager.writer_queue:
                        # cancel installation
                        self.item.download.dlmanager.writer_queue.put_nowait(WriterTask("", kill=True))

                    # forcibly kill DL workers that are not actually dead yet
                    for child in self.item.download.dlmanager.children:
                        if child.exitcode is None:
                            child.terminate()

                    if self.item.download.dlmanager.shared_memory:
                        # close up shared memory
                        self.item.download.dlmanager.shared_memory.close()
                        self.item.download.dlmanager.shared_memory.unlink()
                        self.item.download.dlmanager.shared_memory = None

                    self.item.download.dlmanager.kill()

                    # force kill any threads that are somehow still alive
                    for proc in psutil.process_iter():
                        # check whether the process name matches
                        if (
                                sys.platform in ["linux", "darwin"]
                                and proc.name() == "DownloadThread"
                        ):
                            proc.kill()
                        elif (
                                sys.platform == "win32"
                                and proc.name() == "python.exe"
                                and proc.create_time() >= start_time
                        ):
                            proc.kill()

                    logger.info("Download stopped. It can be continued later.")
                    dl_stopped = True
                try:
                    if not dl_stopped:
                        self.statistics.emit(self.item.download.dlmanager.status_queue.get(timeout=1))
                except queue.Empty:
                    pass

            self.item.download.dlmanager.join()

        except Exception as e:
            logger.error(
                f"Installation failed after {time.time() - start_time:.02f} seconds: {e}"
            )
            self.status.emit(f"error {e}")
            return

        else:
            if dl_stopped:
                return
            self.status.emit("dl_finished")
            end_t = time.time()
            logger.info(f"Download finished in {end_t - start_time}s")

            if self.item.options.overlay:
                self.signals.overlay_installation_finished.emit()
                self.core.finish_overlay_install(self.item.download.igame)
                self.status.emit("finish")
                return

            if not self.item.options.no_install:
                postinstall = self.core.install_game(self.item.download.igame)
                if postinstall:
                    self._handle_postinstall(postinstall, self.item.download.igame)

                dlcs = self.core.get_dlc_for_game(self.item.download.igame.app_name)
                if dlcs:
                    print("The following DLCs are available for this game:")
                    for dlc in dlcs:
                        print(
                            f" - {dlc.app_title} (App name: {dlc.app_name}, version: {dlc.app_version})"
                        )
                    print(
                        "Manually installing DLCs works the same; just use the DLC app name instead."
                    )

                if self.item.download.game.supports_cloud_saves and not self.item.download.game.is_dlc:
                    logger.info(
                        'This game supports cloud saves, syncing is handled by the "sync-saves" command.'
                    )
                    logger.info(
                        f'To download saves for this game run "legendary sync-saves {self.item.download.game.app_name}"'
                    )

        LegendaryCLISingleton().clean_post_install(
            self.item.download.game, self.item.download.igame,
            self.item.download.repair, self.item.download.repair_file
        )

        if not self.item.options.update and self.item.options.create_shortcut:
            if not create_desktop_link(self.item.options.app_name, self.core, "desktop"):
                # maybe add it to download summary, to show in finished downloads
                pass
            else:
                logger.info("Desktop shortcut written")

        self.status.emit("finish")

    def _handle_postinstall(self, postinstall, igame):
        logger.info(f"Postinstall info: {postinstall}")
        if platform.system() == "Windows":
            if self.item.options.install_preqs:
                self.core.prereq_installed(igame.app_name)
                req_path, req_exec = os.path.split(postinstall["path"])
                work_dir = os.path.join(igame.install_path, req_path)
                fullpath = os.path.join(work_dir, req_exec)
                proc = QProcess()
                proc.setProcessChannelMode(QProcess.MergedChannels)
                proc.readyReadStandardOutput.connect(
                    lambda: logger.debug(
                        str(proc.readAllStandardOutput().data(), "utf-8", "ignore")
                    ))
                proc.start(fullpath, postinstall.get("args", []))
                proc.waitForFinished()  # wait, because it is inside the thread
            else:
                self.core.prereq_installed(self.item.download.igame.app_name)
        else:
            logger.info("Automatic installation not available on Linux.")

    def kill(self):
        self._kill = True

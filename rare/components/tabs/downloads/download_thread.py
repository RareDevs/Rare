import os
import platform
import queue
import time
from dataclasses import dataclass
from enum import IntEnum
from logging import getLogger
from typing import List, Optional, Dict

from PyQt5.QtCore import QThread, pyqtSignal, QProcess
from legendary.core import LegendaryCore

from rare.lgndr.api_monkeys import DLManagerSignals
from rare.lgndr.cli import LegendaryCLI
from rare.lgndr.downloading import UIUpdate
from rare.models.install import InstallQueueItemModel
from rare.shared import GlobalSignalsSingleton, ArgumentsSingleton

logger = getLogger("DownloadThread")


class DownloadThread(QThread):
    @dataclass
    class ReturnStatus:
        class ReturnCode(IntEnum):
            ERROR = 1
            STOPPED = 2
            FINISHED = 3

        app_name: str
        ret_code: ReturnCode = ReturnCode.ERROR
        message: str = ""
        dlcs: Optional[List[Dict]] = None
        sync_saves: bool = False
        tip_url: str = ""
        shortcuts: bool = False

    ret_status = pyqtSignal(ReturnStatus)
    ui_update = pyqtSignal(UIUpdate)

    def __init__(self, core: LegendaryCore, item: InstallQueueItemModel):
        super(DownloadThread, self).__init__()
        self.signals = GlobalSignalsSingleton()
        self.core: LegendaryCore = core
        self.item: InstallQueueItemModel = item
        self.dlm_signals: DLManagerSignals = DLManagerSignals()

    def run(self):
        cli = LegendaryCLI(self.core)
        self.item.download.dlm.logging_queue = cli.logging_queue
        self.item.download.dlm.proc_debug = ArgumentsSingleton().debug
        ret = DownloadThread.ReturnStatus(self.item.download.game.app_name)
        start_t = time.time()
        try:
            self.item.download.dlm.start()
            time.sleep(1)
            while self.item.download.dlm.is_alive():
                try:
                    self.ui_update.emit(self.item.download.dlm.status_queue.get(timeout=1.0))
                except queue.Empty:
                    pass
                if self.dlm_signals.update:
                    try:
                        self.item.download.dlm.signals_queue.put(self.dlm_signals, block=False, timeout=1.0)
                    except queue.Full:
                        pass
                time.sleep(self.item.download.dlm.update_interval / 10)
            self.item.download.dlm.join()
        except Exception as e:
            end_t = time.time()
            logger.error(f"Installation failed after {end_t - start_t:.02f} seconds.")
            logger.warning(f"The following exception occurred while waiting for the downloader to finish: {e!r}.")
            ret.ret_code = ret.ReturnCode.ERROR
            ret.message = f"{e!r}"
            self.ret_status.emit(ret)
            return
        else:
            end_t = time.time()
            if self.dlm_signals.kill is True:
                logger.info(f"Download stopped after {end_t - start_t:.02f} seconds.")
                ret.ret_code = ret.ReturnCode.STOPPED
                self.ret_status.emit(ret)
                return
            logger.info(f"Download finished in {end_t - start_t:.02f} seconds.")

            ret.ret_code = ret.ReturnCode.FINISHED

            if self.item.options.overlay:
                self.signals.overlay_installation_finished.emit()
                self.core.finish_overlay_install(self.item.download.igame)
                self.ret_status.emit(ret)
                return

            if not self.item.options.no_install:
                postinstall = self.core.install_game(self.item.download.igame)
                if postinstall:
                    # LegendaryCLI(self.core)._handle_postinstall(
                    #     postinstall,
                    #     self.item.download.igame,
                    #     False,
                    #     self.item.options.install_prereqs,
                    # )
                    self._handle_postinstall(postinstall, self.item.download.igame)

                dlcs = self.core.get_dlc_for_game(self.item.download.igame.app_name)
                if dlcs and not self.item.options.skip_dlcs:
                    ret.dlcs = []
                    for dlc in dlcs:
                        ret.dlcs.append(
                            {
                                "app_name": dlc.app_name,
                                "app_title": dlc.app_title,
                                "app_version": dlc.app_version(self.item.options.platform),
                            }
                        )

                if (
                    self.item.download.game.supports_cloud_saves
                    or self.item.download.game.supports_mac_cloud_saves
                ) and not self.item.download.game.is_dlc:
                    ret.sync_saves = True

                # show tip again after installation finishes so users hopefully actually see it
                if tip_url := self.core.get_game_tip(self.item.download.igame.app_name):
                    ret.tip_url = tip_url

            LegendaryCLI(self.core).install_game_cleanup(
                self.item.download.game,
                self.item.download.igame,
                self.item.download.repair,
                self.item.download.repair_file,
            )

            if not self.item.options.update and self.item.options.create_shortcut:
                ret.shortcuts = True

        self.ret_status.emit(ret)

    def _handle_postinstall(self, postinstall, igame):
        logger.info("This game lists the following prerequisites to be installed:")
        logger.info(f'- {postinstall["name"]}: {" ".join((postinstall["path"], postinstall["args"]))}')
        if platform.system() == "Windows":
            if self.item.options.install_prereqs:
                logger.info("Launching prerequisite executable..")
                self.core.prereq_installed(igame.app_name)
                req_path, req_exec = os.path.split(postinstall["path"])
                work_dir = os.path.join(igame.install_path, req_path)
                fullpath = os.path.join(work_dir, req_exec)
                proc = QProcess()
                proc.setProcessChannelMode(QProcess.MergedChannels)
                proc.readyReadStandardOutput.connect(
                    lambda: logger.debug(str(proc.readAllStandardOutput().data(), "utf-8", "ignore"))
                )
                proc.setProgram(fullpath)
                proc.setArguments(postinstall.get("args", "").split(" "))
                proc.setWorkingDirectory(work_dir)
                proc.start()
                proc.waitForFinished()  # wait, because it is inside the thread
        else:
            logger.info("Automatic installation not available on Linux.")

    def kill(self):
        self.dlm_signals.kill = True

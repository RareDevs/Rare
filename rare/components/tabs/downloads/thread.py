import os
import platform
import queue
import time
from dataclasses import dataclass
from enum import IntEnum
from logging import getLogger
from typing import List, Optional, Dict

from PyQt5.QtCore import QThread, pyqtSignal, QProcess

from rare.lgndr.cli import LegendaryCLI
from rare.lgndr.core import LegendaryCore
from rare.lgndr.glue.monkeys import DLManagerSignals
from rare.lgndr.models.downloading import UIUpdate
from rare.models.game import RareGame
from rare.models.install import InstallQueueItemModel, InstallOptionsModel

logger = getLogger("DownloadThread")


class DlResultCode(IntEnum):
    ERROR = 1
    STOPPED = 2
    FINISHED = 3


@dataclass
class DlResultModel:
    options: InstallOptionsModel
    code: DlResultCode = DlResultCode.ERROR
    message: str = ""
    dlcs: Optional[List[Dict]] = None
    sync_saves: bool = False
    tip_url: str = ""
    shortcut: bool = False
    shortcut_name: str = ""
    shortcut_title: str = ""


class DlThread(QThread):
    result = pyqtSignal(DlResultModel)
    progress = pyqtSignal(UIUpdate, object)

    def __init__(self, item: InstallQueueItemModel, rgame: RareGame, core: LegendaryCore, debug: bool = False):
        super(DlThread, self).__init__()
        self.dlm_signals: DLManagerSignals = DLManagerSignals()
        self.core: LegendaryCore = core
        self.item: InstallQueueItemModel = item
        self.dl_size = item.download.analysis.dl_size
        self.rgame = rgame
        self.debug = debug

    def __finish(self, result):
        if result.code == DlResultCode.FINISHED:
            self.rgame.set_installed(True)
        self.rgame.state = RareGame.State.IDLE
        self.rgame.signals.progress.finish.emit(not result.code == DlResultCode.FINISHED)
        self.result.emit(result)

    def run(self):
        cli = LegendaryCLI(self.core)
        self.item.download.dlm.logging_queue = cli.logging_queue
        self.item.download.dlm.proc_debug = self.debug
        result = DlResultModel(self.item.options)
        start_t = time.time()
        try:
            self.item.download.dlm.start()
            self.rgame.state = RareGame.State.DOWNLOADING
            self.rgame.signals.progress.start.emit()
            time.sleep(1)
            while self.item.download.dlm.is_alive():
                try:
                    status = self.item.download.dlm.status_queue.get(timeout=1.0)
                    self.rgame.signals.progress.update.emit(int(status.progress))
                    self.progress.emit(status, self.dl_size)
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
            self.kill()
            self.item.download.dlm.join()
            end_t = time.time()
            logger.error(f"Installation failed after {end_t - start_t:.02f} seconds.")
            logger.warning(f"The following exception occurred while waiting for the downloader to finish: {e!r}.")
            result.code = DlResultCode.ERROR
            result.message = f"{e!r}"
            self.__finish(result)
            return
        else:
            end_t = time.time()
            if self.dlm_signals.kill is True:
                logger.info(f"Download stopped after {end_t - start_t:.02f} seconds.")
                result.code = DlResultCode.STOPPED
                self.__finish(result)
                return
            logger.info(f"Download finished in {end_t - start_t:.02f} seconds.")

            result.code = DlResultCode.FINISHED

            if self.item.options.overlay:
                self.core.finish_overlay_install(self.item.download.igame)
                self.__finish(result)
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
                    result.dlcs = []
                    for dlc in dlcs:
                        result.dlcs.append(
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
                    result.sync_saves = True

                # show tip again after installation finishes so users hopefully actually see it
                if tip_url := self.core.get_game_tip(self.item.download.igame.app_name):
                    result.tip_url = tip_url

            LegendaryCLI(self.core).install_game_cleanup(
                self.item.download.game,
                self.item.download.igame,
                self.item.download.repair,
                self.item.download.repair_file,
            )

            if not self.item.options.update and self.item.options.create_shortcut:
                result.shortcut = True
                result.shortcut_name = self.rgame.folder_name
                result.shortcut_title = self.rgame.app_title

        self.__finish(result)

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

import multiprocessing
import os
import platform
import queue
import threading
import time
from dataclasses import dataclass
from enum import IntEnum
from logging import getLogger
from typing import Dict, List, Optional

from PySide6.QtCore import QProcess, QThread, Signal

from rare.lgndr.cli import LegendaryCLI
from rare.lgndr.core import LegendaryCore
from rare.lgndr.glue.monkeys import DLManagerSignals
from rare.lgndr.models.downloading import UIUpdate
from rare.models.game import RareGame
from rare.models.install import InstallOptionsModel, InstallQueueItemModel


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
    folder_name: str = ""
    app_title: str = ""


class DlThread(QThread):
    result = Signal(DlResultModel)
    progress = Signal(UIUpdate, object)

    def __init__(
        self,
        item: InstallQueueItemModel,
        rgame: RareGame,
        core: LegendaryCore,
        debug: bool = False,
    ):
        super(DlThread, self).__init__()
        self.logger = getLogger(type(self).__name__)
        self.dlm_signals: DLManagerSignals = DLManagerSignals()
        self.core: LegendaryCore = core
        self.item: InstallQueueItemModel = item
        self.dl_size = item.download.analysis.dl_size
        self.rgame = rgame
        self.debug = debug

    def _finish(self, result):
        if result.code == DlResultCode.FINISHED and not result.options.no_install:
            self.rgame.set_installed(True)
        self.rgame.state = RareGame.State.IDLE
        self.rgame.signals.progress.finish.emit(result.code != DlResultCode.FINISHED)
        self.result.emit(result)
        self.quit()

    def _status_callback(self, status: UIUpdate):
        self.progress.emit(status, self.dl_size)
        self.rgame.signals.progress.refresh.emit(int(status.progress))

    def run(self):
        cli = LegendaryCLI(self.core)
        result = DlResultModel(self.item.options)
        result.app_title = self.rgame.app_title

        ticket_a, ticket_b = multiprocessing.Pipe()
        sign_a, sign_b = multiprocessing.Pipe()

        def ticket_creator_thread():
            t = threading.current_thread()
            while not getattr(t, "stop", False):
                if ticket_b.poll(1):
                    catalog_item_id, build_version, app_name, namespace, label, platform = ticket_b.recv()
                    ticket_b.send(
                        self.core.egs.get_download_ticket(catalog_item_id, build_version, app_name, namespace, label, platform)
                    )

        def chunk_url_sign_thread():
            t = threading.current_thread()
            while not getattr(t, "stop", False):
                if sign_b.poll(1):
                    ticket, chunk_paths = sign_b.recv()
                    signed_chunk_urls = self.core.egs.get_signed_chunk_urls(ticket, chunk_paths)
                    if self.item.options.disable_https:
                        for key in signed_chunk_urls:
                            signed_chunk_urls[key] = signed_chunk_urls[key].replace("https://", "http://")
                    sign_b.send(signed_chunk_urls)

        ticket_thread = threading.Thread(target=ticket_creator_thread)
        sign_thread = threading.Thread(target=chunk_url_sign_thread)

        start_t = time.time()
        try:
            self.item.download.dlm.logging_queue = cli.logging_queue
            self.item.download.dlm.proc_debug = self.debug
            self.item.download.dlm.ticket_pipe = ticket_a
            self.item.download.dlm.sign_pipe = sign_a

            ticket_thread.start()
            sign_thread.start()
            self.item.download.dlm.start()
            self.rgame.state = RareGame.State.DOWNLOADING
            self.rgame.signals.progress.start.emit()
            time.sleep(1)
            while self.item.download.dlm.is_alive():
                try:
                    self._status_callback(self.item.download.dlm.status_queue.get(timeout=1.0))
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
            self.logger.error(f"Installation failed after {end_t - start_t:.02f} seconds.")
            self.logger.warning(f"The following exception occurred while waiting for the downloader to finish: {e!r}.")
            result.code = DlResultCode.ERROR
            result.message = f"{e!r}"
            return
        else:
            end_t = time.time()
            if self.dlm_signals.kill:
                self.logger.info(f"Download stopped after {end_t - start_t:.02f} seconds.")
                result.code = DlResultCode.STOPPED
                return
            self.logger.info(f"Download finished in {end_t - start_t:.02f} seconds.")

            result.code = DlResultCode.FINISHED

            if self.item.options.overlay:
                self.core.finish_overlay_install(self.item.download.igame)
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
                    result.dlcs.extend(
                        {
                            "app_name": dlc.app_name,
                            "app_title": dlc.app_title,
                            "app_version": dlc.app_version(self.item.options.platform),
                        }
                        for dlc in dlcs
                    )
                if (
                    self.item.download.game.supports_cloud_saves or self.item.download.game.supports_mac_cloud_saves
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

            result.shortcut = not self.item.options.update and self.item.options.create_shortcut
            result.folder_name = self.rgame.folder_name

            return
        finally:
            ticket_thread.stop = True
            sign_thread.stop = True
            ticket_thread.join()
            sign_thread.join()
            self._finish(result)

    def _handle_postinstall(self, postinstall, igame):
        self.logger.info("This game lists the following prerequisites to be installed:")
        self.logger.info(f"- {postinstall['name']}: {' '.join((postinstall['path'], postinstall['args']))}")
        if platform.system() == "Windows":
            if self.item.options.install_prereqs:
                self.logger.info("Launching prerequisite executable..")
                self.core.prereq_installed(igame.app_name)
                req_path, req_exec = os.path.split(postinstall["path"])
                work_dir = os.path.join(igame.install_path, req_path)
                fullpath = os.path.join(work_dir, req_exec)
                proc = QProcess(self)
                proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
                proc.readyReadStandardOutput.connect(
                    (lambda obj: obj.logger.debug(
                        str(proc.readAllStandardOutput().data(), "utf-8", "ignore"))).__get__(self)
                )
                proc.setProgram(fullpath)
                proc.setArguments(postinstall.get("args", "").split(" "))
                proc.setWorkingDirectory(work_dir)
                proc.start()
                proc.waitForFinished()  # wait, because it is inside the thread
        else:
            self.logger.info("Automatic installation not available on Linux.")

    def kill(self):
        self.dlm_signals.kill = True

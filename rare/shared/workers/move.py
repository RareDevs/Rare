import os
import shutil
from enum import auto
from typing import Iterator

from legendary.lfs.utils import validate_files
from legendary.models.game import VerifyResult
from PySide6.QtCore import QObject, Signal

from rare.lgndr.core import LegendaryCore
from rare.models.game import RareGame
from rare.models.install import MoveGameModel
from rare.utils.misc import path_size
from rare.widgets.indicator_edit import IndicatorReasons, IndicatorReasonsCommon

from .worker import QueueWorker, QueueWorkerInfo, Worker


class MovePathEditReasons(IndicatorReasons):
    MOVEDIALOG_DST_MISSING = auto()
    MOVEDIALOG_NO_WRITE = auto()
    MOVEDIALOG_SAME_DIR = auto()
    MOVEDIALOG_DST_IN_SRC = auto()
    MOVEDIALOG_NESTED_DIR = auto()
    MOVEDIALOG_NO_SPACE = auto()


class MoveInfoWorker(Worker):
    class Signals(QObject):
        result: Signal = Signal(bool, object, object, MovePathEditReasons)

    def __init__(self, rgame: RareGame, igames: Iterator[RareGame], options: MoveGameModel):
        super(MoveInfoWorker, self).__init__()
        self.signals = MoveInfoWorker.Signals()

        self.rgame: RareGame = rgame
        self.installed_games: Iterator[RareGame] = igames
        self.target_path: str = options.target_path
        self.full_path: str = options.target_path if options.rename_path else options.full_path

    @staticmethod
    def is_game_dir(src_path: str, dst_path: str):
        # This iterates over the destination dir, then iterates over the current install dir and if the file names
        # matches, we have an exisiting dir
        if os.path.isdir(dst_path):
            for dst_file in os.listdir(dst_path):
                for src_file in os.listdir(src_path):
                    if dst_file == src_file:
                        return True
        return False

    def run_real(self):
        if not self.rgame.install_path or not self.full_path:
            self.signals.result.emit(False, 0, 0, MovePathEditReasons.MOVEDIALOG_DST_MISSING)
            return

        src_path = os.path.realpath(self.rgame.install_path)
        dst_path = os.path.realpath(self.full_path)
        tgt_path = os.path.realpath(self.target_path)
        dst_install_path = os.path.realpath(os.path.join(dst_path, os.path.basename(src_path)))

        # Get free space on drive and size of game folder
        _, _, dst_size = shutil.disk_usage(tgt_path)
        src_size = path_size(src_path)

        if src_path in {dst_path, dst_install_path}:
            self.signals.result.emit(False, src_size, dst_size, MovePathEditReasons.MOVEDIALOG_SAME_DIR)
            return

        if str(src_path) in str(dst_path):
            self.signals.result.emit(False, src_size, dst_size, MovePathEditReasons.MOVEDIALOG_DST_IN_SRC)
            return

        if str(dst_install_path) in str(src_path):
            self.signals.result.emit(False, src_size, dst_size, MovePathEditReasons.MOVEDIALOG_DST_IN_SRC)
            return

        for rgame in self.installed_games:
            if not rgame.is_non_asset and rgame.install_path in self.full_path:
                self.signals.result.emit(False, src_size, dst_size, MovePathEditReasons.MOVEDIALOG_NESTED_DIR)
                return

        is_existing_dir = self.is_game_dir(src_path, dst_install_path)
        # for item in os.listdir(dst_path):
        #     if os.path.basename(src_path) in os.path.basename(item):
        #         if os.path.isdir(dst_install_path):
        #             if not is_existing_dir:
        #                 self.ui.warning_text.setHidden(False)
        #         elif os.path.isfile(dst_install_path):
        #             self.ui.warning_text.setHidden(False)

        if dst_size <= src_size and not is_existing_dir:
            self.signals.result.emit(False, src_size, dst_size, MovePathEditReasons.MOVEDIALOG_NO_SPACE)
            return

        self.signals.result.emit(True, src_size, dst_size, IndicatorReasonsCommon.VALID)
        return


class MoveWorkerSignals(QObject):
    # int: percentage, object: source size, object: dest size
    progress = Signal(RareGame, int, object, object)
    # str: destination path
    result = Signal(RareGame, str)
    # str: error message
    error = Signal(RareGame, str)


class MoveWorker(QueueWorker):

    def __init__(self, core: LegendaryCore, rgame: RareGame, options: MoveGameModel):
        super(MoveWorker, self).__init__()
        self.signals = MoveWorkerSignals()
        self.core = core
        self.rgame = rgame
        self.options: MoveGameModel = options
        self.dst_path: str = options.full_path
        self.dst_exists: bool = options.dst_exists

        # set RareGame's state as soon as the worker is instantiated to avoid conflicts
        self.rgame.state = RareGame.State.MOVING

    def worker_info(self) -> QueueWorkerInfo:
        return QueueWorkerInfo(
            app_name=self.rgame.app_name,
            app_title=self.rgame.app_title,
            type=type(self).__name__,
            prefix="Moving",
            state=self.state,
        )

    def progress(self, src_size, dst_size):
        progress = dst_size * 100 // src_size
        self.rgame.signals.progress.update.emit(progress)
        self.signals.progress.emit(self.rgame, progress, src_size, dst_size)

    def run_real(self):
        self.rgame.signals.progress.start.emit()

        if self.options.dst_delete:
            if os.path.isdir(self.options.full_path):
                shutil.rmtree(self.options.full_path)
            else:
                os.remove(self.options.full_path)

        if os.stat(self.rgame.install_path).st_dev == os.stat(os.path.dirname(self.dst_path)).st_dev:
            os.makedirs(self.dst_path, exist_ok=True)
            for src in os.listdir(self.rgame.install_path):
                shutil.move(os.path.join(self.rgame.install_path, src), self.dst_path)
            os.rmdir(self.rgame.install_path)

        elif not self.dst_exists:
            src_size = sum(
                os.stat(os.path.join(dp, f)).st_size for dp, dn, filenames in os.walk(self.rgame.install_path) for f in filenames
            )
            dst_size = 0

            def copy_with_progress(src, dst):
                nonlocal dst_size
                shutil.copy2(src, dst)
                dst_size += os.stat(src).st_size
                self.progress(src_size, dst_size)

            shutil.copytree(
                self.rgame.install_path,
                self.dst_path,
                copy_function=copy_with_progress,
                dirs_exist_ok=True,
            )
            shutil.rmtree(self.rgame.install_path)

        else:
            manifest_data, _ = self.core.get_installed_manifest(self.rgame.app_name)
            manifest = self.core.load_manifest(manifest_data)
            files = sorted(
                manifest.file_manifest_list.elements,
                key=lambda a: a.filename.lower(),
            )
            if config_tags := self.core.lgd.config.get(self.rgame.app_name, "install_tags", fallback=None):
                install_tags = set(i.strip() for i in config_tags.split(","))
                file_list = [
                    (f.filename, f.sha_hash.hex())
                    for f in files
                    if any(it in install_tags for it in f.install_tags) or not f.install_tags
                ]
            else:
                file_list = [(f.filename, f.sha_hash.hex()) for f in files]

            total_size = sum(manifest.file_manifest_list.get_file_by_path(fm[0]).file_size for fm in file_list)
            dst_size = 0

            # This method is a copy_func, and only copies the src if it's a dir.
            # Thus, it can be used to re-create the dir structure.
            def copy_dir_structure(src, dst):
                if os.path.isdir(dst):
                    dst = os.path.join(dst, os.path.basename(src))
                if os.path.isdir(src):
                    shutil.copyfile(src, dst)
                    shutil.copystat(src, dst)
                return dst

            # recreate dir structure
            shutil.copytree(
                self.rgame.install_path,
                self.dst_path,
                copy_function=copy_dir_structure,
                dirs_exist_ok=True,
            )

            for result, path, _, _ in validate_files(self.dst_path, file_list):
                dst_path = os.path.join(self.dst_path, path)
                src_path = os.path.join(self.rgame.install_path, path)
                if os.path.isfile(src_path):
                    if result == VerifyResult.HASH_MATCH:
                        dst_size += os.stat(dst_path).st_size
                    if result == VerifyResult.HASH_MISMATCH or result == VerifyResult.FILE_MISSING:
                        try:
                            shutil.copy2(src_path, dst_path)
                            dst_size += os.stat(dst_path).st_size
                        except (IOError, OSError) as e:
                            self.rgame.signals.progress.finish.emit(True)
                            self.signals.error.emit(self.rgame, str(e))
                            return
                    else:
                        self.logger.warning(f"Copying file {src_path} to {dst_path} failed")
                    self.progress(total_size, dst_size)
                else:
                    self.logger.warning(f"Source dir does not have file {src_path}. File will be missing in the destination dir.")
                    self.rgame.needs_verification = True
            shutil.rmtree(self.rgame.install_path)

        self.rgame.install_path = self.dst_path

        self.rgame.signals.progress.finish.emit(False)
        self.signals.result.emit(self.rgame, self.dst_path)

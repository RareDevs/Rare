import os
import shutil
from logging import getLogger

from PyQt5.QtCore import pyqtSignal, QObject
from legendary.lfs.utils import validate_files
from legendary.models.game import VerifyResult

from rare.models.game import RareGame
from rare.lgndr.core import LegendaryCore
from .worker import QueueWorker, QueueWorkerInfo

logger = getLogger("MoveWorker")


class MoveWorker(QueueWorker):
    class Signals(QObject):
        # int: percentage, object: source size, object: dest size
        progress = pyqtSignal(RareGame, int, object, object)
        # str: destination path
        result = pyqtSignal(RareGame, str)
        # str: error message
        error = pyqtSignal(RareGame, str)

    def __init__(self, core: LegendaryCore, rgame: RareGame, dst_path: str, dst_exists: bool):
        super(MoveWorker, self).__init__()
        self.signals = MoveWorker.Signals()
        self.core = core
        self.rgame = rgame
        self.dst_path = dst_path
        self.dst_exists = dst_exists

    def worker_info(self) -> QueueWorkerInfo:
        return QueueWorkerInfo(
            app_name=self.rgame.app_name, app_title=self.rgame.app_title, worker_type="Move", state=self.state
        )

    def progress(self, src_size, dst_size):
        progress = dst_size * 100 // src_size
        self.rgame.signals.progress.update.emit(progress)
        self.signals.progress.emit(self.rgame, progress, src_size, dst_size)

    def run_real(self):
        self.rgame.signals.progress.start.emit()

        if os.stat(self.rgame.install_path).st_dev == os.stat(os.path.dirname(self.dst_path)).st_dev:
            shutil.move(self.rgame.install_path, self.dst_path)

        elif not self.dst_exists:
            src_size = sum(
                os.stat(os.path.join(dp, f)).st_size
                for dp, dn, filenames in os.walk(self.rgame.install_path)
                for f in filenames
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
            if config_tags := self.core.lgd.config.get(self.rgame.app_name, 'install_tags', fallback=None):
                install_tags = set(i.strip() for i in config_tags.split(','))
                file_list = [
                    (f.filename, f.sha_hash.hex())
                    for f in files
                    if any(it in install_tags for it in f.install_tags) or not f.install_tags
                ]
            else:
                file_list = [(f.filename, f.sha_hash.hex()) for f in files]

            total_size = sum(manifest.file_manifest_list.get_file_by_path(fm[0]).file_size
                             for fm in file_list)
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
                        logger.warning(f"Copying file {src_path} to {dst_path} failed")
                    self.progress(total_size, dst_size)
                else:
                    logger.warning(
                        f"Source dir does not have file {src_path}. File will be missing in the destination dir."
                    )
                    self.rgame.needs_verification = True
            shutil.rmtree(self.rgame.install_path)

        self.rgame.install_path = self.dst_path

        self.rgame.signals.progress.finish.emit(False)
        self.signals.result.emit(self.rgame, self.dst_path)

import os
import shutil
from pathlib import Path

from PyQt5.QtCore import pyqtSignal, QRunnable, QObject
from legendary.lfs.utils import validate_files
from legendary.models.game import VerifyResult, InstalledGame

from rare.lgndr.core import LegendaryCore
from .worker import Worker


# noinspection PyUnresolvedReferences
class MoveWorker(Worker):
    class Signals(QObject):
        progress = pyqtSignal(int)
        finished = pyqtSignal(str)
        no_space_left = pyqtSignal()

    def __init__(
            self,
            core: LegendaryCore,
            install_path: str,
            dest_path: Path,
            is_existing_dir: bool,
            igame: InstalledGame,
    ):
        super(MoveWorker, self).__init__()
        self.signals = MoveWorker.Signals()
        self.core = core
        self.install_path = install_path
        self.dest_path = dest_path
        self.source_size = 0
        self.dest_size = 0
        self.is_existing_dir = is_existing_dir
        self.igame = igame
        self.file_list = None
        self.total: int = 0

    def run_real(self):
        root_directory = Path(self.install_path)
        self.source_size = sum(f.stat().st_size for f in root_directory.glob("**/*") if f.is_file())

        # if game dir is not existing, just copying:
        if not self.is_existing_dir:
            shutil.copytree(
                self.install_path,
                self.dest_path,
                copy_function=self.copy_each_file_with_progress,
                dirs_exist_ok=True,
            )
        else:
            manifest_data, _ = self.core.get_installed_manifest(self.igame.app_name)
            manifest = self.core.load_manifest(manifest_data)
            files = sorted(
                manifest.file_manifest_list.elements,
                key=lambda a: a.filename.lower(),
            )
            self.file_list = [(f.filename, f.sha_hash.hex()) for f in files]
            self.total = len(self.file_list)

            # recreate dir structure
            shutil.copytree(
                self.install_path,
                self.dest_path,
                copy_function=self.copy_dir_structure,
                dirs_exist_ok=True,
            )

            for i, (result, relative_path, _, _) in enumerate(
                    validate_files(str(self.dest_path), self.file_list)
            ):
                dst_path = f"{self.dest_path}/{relative_path}"
                src_path = f"{self.install_path}/{relative_path}"
                if Path(src_path).is_file():
                    if result == VerifyResult.HASH_MISMATCH:
                        try:
                            shutil.copy(src_path, dst_path)
                        except IOError:
                            self.signals.no_space_left.emit()
                            return
                    elif result == VerifyResult.FILE_MISSING:
                        try:
                            shutil.copy(src_path, dst_path)
                        except (IOError, OSError):
                            self.signals.no_space_left.emit()
                            return
                    elif result == VerifyResult.OTHER_ERROR:
                        logger.warning(f"Copying file {src_path} to {dst_path} failed")
                    self.signals.progress.emit(int(i * 10 / self.total * 10))
                else:
                    logger.warning(
                        f"Source dir does not have file {src_path}. File will be missing in the destination "
                        f"dir. "
                    )

        shutil.rmtree(self.install_path)
        self.signals.finished.emit(str(self.dest_path))

    def copy_each_file_with_progress(self, src, dst):
        shutil.copy(src, dst)
        self.dest_size += Path(src).stat().st_size
        self.signals.progress.emit(int(self.dest_size * 10 / self.source_size * 10))

    # This method is a copy_func, and only copies the src if it's a dir.
    # Thus, it can be used to re-create the dir strucute.
    @staticmethod
    def copy_dir_structure(src, dst):
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))
        if os.path.isdir(src):
            shutil.copyfile(src, dst)
            shutil.copystat(src, dst)
        return dst

import os
import shutil
from logging import getLogger
from sys import stdout

from PyQt5.QtCore import QProcess, QProcessEnvironment, QThread, pyqtSignal

from custom_legendary.core import LegendaryCore
from custom_legendary.models.game import VerifyResult
from custom_legendary.utils.lfs import validate_files

logger = getLogger("Legendary Utils")


def launch_game(core, app_name: str, offline: bool = False, skip_version_check: bool = False):
    game = core.get_installed_game(app_name)
    if not game:
        print("Game not found")
        return None
    if game.is_dlc:
        print("Game is dlc")
        return None
    if not os.path.exists(game.install_path):
        print("Game doesn't exist")
        return None

    if not offline:

        if not skip_version_check and not core.is_noupdate_game(app_name):
            # check updates
            try:
                latest = core.get_asset(app_name, update=True)
            except ValueError:
                print("Metadata doesn't exist")
                return None
            if latest.build_version != game.version:
                print("Please update game")
                return None
    params, cwd, env = core.get_launch_parameters(app_name=app_name, offline=offline)

    process = QProcess()
    process.setProcessChannelMode(QProcess.MergedChannels)
    process.setWorkingDirectory(cwd)
    environment = QProcessEnvironment()
    for e in env:
        environment.insert(e, env[e])
    process.setProcessEnvironment(environment)

    return process, params


def uninstall(app_name: str, core, options=None):
    if not options:
        options = {"keep_files": False}
    igame = core.get_installed_game(app_name)
    try:
        # Remove DLC first so directory is empty when game uninstall runs
        dlcs = core.get_dlc_for_game(app_name)
        for dlc in dlcs:
            if (idlc := core.get_installed_game(dlc.app_name)) is not None:
                logger.info(f'Uninstalling DLC "{dlc.app_name}"...')
                core.uninstall_game(idlc, delete_files=not options["keep_files"])

        logger.info(f'Removing "{igame.title}" from "{igame.install_path}"...')
        core.uninstall_game(igame, delete_files=not options["keep_files"], delete_root_directory=True)
        logger.info('Game has been uninstalled.')
        if not options["keep_files"]:
            shutil.rmtree(igame.install_path)

    except Exception as e:
        logger.warning(f'Removing game failed: {e!r}, please remove {igame.install_path} manually.')


class VerifyThread(QThread):
    status = pyqtSignal(tuple)
    summary = pyqtSignal(tuple)

    def __init__(self, core, app_name):
        super(VerifyThread, self).__init__()
        self.core, self.app_name = core, app_name

    def run(self):
        if not self.core.is_installed(self.app_name):
            logger.error(f'Game "{self.app_name}" is not installed')
            return

        logger.info(f'Loading installed manifest for "{self.app_name}"')
        igame = self.core.get_installed_game(self.app_name)
        manifest_data, _ = self.core.get_installed_manifest(self.app_name)
        manifest = self.core.load_manifest(manifest_data)

        files = sorted(manifest.file_manifest_list.elements,
                       key=lambda a: a.filename.lower())

        # build list of hashes
        file_list = [(f.filename, f.sha_hash.hex()) for f in files]
        self.total = len(file_list)
        self.num = 0
        failed = []
        missing = []

        logger.info(f'Verifying "{igame.title}" version "{manifest.meta.build_version}"')
        repair_file = []
        for result, path, result_hash in validate_files(igame.install_path, file_list):
            self.status.emit((self.num, self.total, self.app_name))
            self.num += 1

            if result == VerifyResult.HASH_MATCH:
                repair_file.append(f'{result_hash}:{path}')
                continue
            elif result == VerifyResult.HASH_MISMATCH:
                logger.error(f'File does not match hash: "{path}"')
                repair_file.append(f'{result_hash}:{path}')
                failed.append(path)
            elif result == VerifyResult.FILE_MISSING:
                logger.error(f'File is missing: "{path}"')
                missing.append(path)
            else:
                logger.error(f'Other failure (see log), treating file as missing: "{path}"')
                missing.append(path)

        stdout.write(f'Verification progress: {self.num}/{self.total} ({self.num * 100 / self.total:.01f}%)\t\n')

        # always write repair file, even if all match
        if repair_file:
            repair_filename = os.path.join(self.core.lgd.get_tmp_path(), f'{self.app_name}.repair')
            with open(repair_filename, 'w') as f:
                f.write('\n'.join(repair_file))
            logger.debug(f'Written repair file to "{repair_filename}"')

        if not missing and not failed:
            logger.info('Verification finished successfully.')
            self.summary.emit((0, 0, self.app_name))

        else:
            logger.error(f'Verification failed, {len(failed)} file(s) corrupted, {len(missing)} file(s) are missing.')
            self.summary.emit((len(failed), len(missing), self.app_name))


def import_game(core: LegendaryCore, app_name: str, path: str):
    logger.info("Import " + app_name)
    game = core.get_game(app_name)
    manifest, igame = core.import_game(game, path)
    exe_path = os.path.join(path, manifest.meta.launch_exe.lstrip('/'))
    total = len(manifest.file_manifest_list.elements)
    found = sum(os.path.exists(os.path.join(path, f.filename))
                for f in manifest.file_manifest_list.elements)
    ratio = found / total
    if not os.path.exists(exe_path):
        logger.error(f"Game {game.app_title} failed to import")
        return False
    if ratio < 0.95:
        logger.error(
            "Game files are missing. It may be not the lates version ore it is corrupt")
        return False
    core.install_game(igame)
    if igame.needs_verification:
        logger.info(logger.info(
            f'NOTE: The game installation will have to be verified before it can be updated '
            f'with legendary. Run "legendary repair {app_name}" to do so.'))

    logger.info("Successfully imported Game: " + game.app_title)
    return True

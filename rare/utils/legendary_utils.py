import os
import platform
import shutil
from logging import getLogger

from PyQt5.QtCore import pyqtSignal, QCoreApplication, QObject, QRunnable
from PyQt5.QtWidgets import QMessageBox

from legendary.core import LegendaryCore
from legendary.models.game import VerifyResult
from legendary.utils.lfs import validate_files

logger = getLogger("Legendary Utils")


def uninstall(app_name: str, core: LegendaryCore, options=None):
    if not options:
        options = {"keep_files": False}
    igame = core.get_installed_game(app_name)

    # remove shortcuts link
    if platform.system() == "Linux":
        if os.path.exists(os.path.expanduser(f"~/Desktop/{igame.title}.desktop")):
            os.remove(os.path.expanduser(f"~/Desktop/{igame.title}.desktop"))
        if os.path.exists(os.path.expanduser(f"~/.local/share/applications/{igame.title}.desktop")):
            os.remove(os.path.expanduser(f"~/.local/share/applications/{igame.title}.desktop"))

    elif platform.system() == "Windows":
        if os.path.exists(os.path.expanduser(f"~/Desktop/{igame.title.split(':')[0]}.lnk")):
            os.remove(os.path.expanduser(f"~/Desktop/{igame.title.split(':')[0]}.lnk"))
        elif os.path.exists(
                os.path.expandvars(f"%appdata%/Microsoft/Windows/Start Menu/{igame.title.split(':')[0]}.lnk")):
            os.remove(os.path.expandvars(f"%appdata%/Microsoft/Windows/Start Menu/{igame.title.split(':')[0]}.lnk"))

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

    logger.info("Removing sections in config file")
    if core.lgd.config.has_section(app_name):
        core.lgd.config.remove_section(app_name)
    if core.lgd.config.has_section(app_name + ".env"):
        core.lgd.config.remove_section(app_name + ".env")
    core.lgd.save_config()


def update_manifest(app_name: str, core: LegendaryCore):
    game = core.get_game(app_name)
    logger.info('Reloading game manifest of ' + game.app_title)
    new_manifest_data, base_urls = core.get_cdn_manifest(game)
    # overwrite base urls in metadata with current ones to avoid using old/dead CDNs
    game.base_urls = base_urls
    # save base urls to game metadata
    core.lgd.set_game_meta(game.app_name, game)

    new_manifest = core.load_manifest(new_manifest_data)
    logger.debug(f'Base urls: {base_urls}')
    # save manifest with version name as well for testing/downgrading/etc.
    core.lgd.save_manifest(game.app_name, new_manifest_data,
                           version=new_manifest.meta.build_version)


class VerifySignals(QObject):
    status = pyqtSignal(tuple)
    summary = pyqtSignal(int, int, str)


class VerifyWorker(QRunnable):
    num: int = 0
    total: int = 1  # set default to 1 to avoid DivisionByZero before it is initialized

    def __init__(self, core, app_name):
        super(VerifyWorker, self).__init__()
        self.core, self.app_name = core, app_name
        self.signals = VerifySignals()
        self.setAutoDelete(True)

    def run(self):
        if not self.core.is_installed(self.app_name):
            logger.error(f'Game "{self.app_name}" is not installed')
            return
        igame = self.core.get_installed_game(self.app_name)

        logger.info(f'Loading installed manifest for "{igame.title}"')
        manifest_data, _ = self.core.get_installed_manifest(self.app_name)
        if not manifest_data:
            update_manifest(self.app_name, self.core)
        manifest_data, _ = self.core.get_installed_manifest(self.app_name)
        if not manifest_data:
            self.signals.summary.emit(-1, -1, self.app_name)
            return

        manifest = self.core.load_manifest(manifest_data)

        files = sorted(manifest.file_manifest_list.elements,
                       key=lambda a: a.filename.lower())

        # build list of hashes
        file_list = [(f.filename, f.sha_hash.hex()) for f in files]
        self.total = len(file_list)
        self.num = 0
        failed = []
        missing = []

        _translate = QCoreApplication.translate

        logger.info(f'Verifying "{igame.title}" version "{manifest.meta.build_version}"')
        repair_file = []
        try:
            for result, path, result_hash in validate_files(igame.install_path, file_list):
                self.signals.status.emit((self.num, self.total, self.app_name))
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
        except OSError as e:
            QMessageBox.warning(None, "Error", _translate("VerifyWorker", "Path does not exist"))
            logger.error(str(e))
        except ValueError as e:
            QMessageBox.warning(None, "Error", _translate("VerifyWorker", "No files to validate"))
            logger.error(str(e))

        # always write repair file, even if all match
        if repair_file:
            repair_filename = os.path.join(self.core.lgd.get_tmp_path(), f'{self.app_name}.repair')
            with open(repair_filename, 'w') as f:
                f.write('\n'.join(repair_file))
            logger.debug(f'Written repair file to "{repair_filename}"')

        if not missing and not failed:
            logger.info('Verification finished successfully.')
            self.signals.summary.emit(0, 0, self.app_name)

        else:
            logger.error(f'Verification finished, {len(failed)} file(s) corrupted, {len(missing)} file(s) are missing.')
            self.signals.summary.emit(len(failed), len(missing), self.app_name)


def import_game(core: LegendaryCore, app_name: str, path: str) -> str:
    _tr = QCoreApplication.translate
    logger.info("Import " + app_name)
    game = core.get_game(app_name, update_meta=False)
    if not game:
        return _tr("LgdUtils", "Could not get game for {}").format(app_name)

    if core.is_installed(app_name):
        logger.error(f"{game.app_title} is already installed")
        return _tr("LgdUtils", "{} is already installed").format(game.app_title)

    if not os.path.exists(path):
        logger.error("Path does not exist")
        return _tr("LgdUtils", "Path does not exist")

    manifest, igame = core.import_game(game, path)
    exe_path = os.path.join(path, manifest.meta.launch_exe.lstrip('/'))

    if not os.path.exists(exe_path):
        logger.error(f"Launch Executable of {game.app_title} does not exist")
        return _tr("LgdUtils", "Launch executable of {} does not exist").format(game.app_title)

    if game.is_dlc:
        release_info = game.metadata.get('mainGameItem', {}).get('releaseInfo')
        if release_info:
            main_game_appname = release_info[0]['appId']
            main_game_title = game.metadata['mainGameItem']['title']
            if not core.is_installed(main_game_appname):
                return _tr("LgdUtils", "Game is a DLC, but {} is not installed").format(main_game_title)
        else:
            return _tr("LgdUtils", "Unable to get base game information for DLC")

    total = len(manifest.file_manifest_list.elements)
    found = sum(os.path.exists(os.path.join(path, f.filename))
                for f in manifest.file_manifest_list.elements)
    ratio = found / total

    if ratio < 0.9:
        logger.warning(
            "Game files are missing. It may be not the latest version or it is corrupt")
        # return False
    core.install_game(igame)
    if igame.needs_verification:
        logger.info(f"{igame.title} needs verification")

    logger.info("Successfully imported Game: " + game.app_title)
    return ""

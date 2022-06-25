import os
import sys

from multiprocessing import Queue
from typing import Callable

from legendary.utils.lfs import validate_files
from legendary.models.downloading import AnalysisResult
from legendary.models.game import *
from legendary.utils.selective_dl import get_sdl_appname

from legendary.core import LegendaryCore as LegendaryCoreReal

from .manager import DLManager
from .exception import LgndrException


class LegendaryCore(LegendaryCoreReal):

    def __log_exception(self, error):
        raise LgndrException(error)

    def prepare_download(self, app_name: str, base_path: str = '',
                         status_q: Queue = None, max_shm: int = 0, max_workers: int = 0,
                         force: bool = False, disable_patching: bool = False,
                         game_folder: str = '', override_manifest: str = '',
                         override_old_manifest: str = '', override_base_url: str = '',
                         platform: str = 'Windows', file_prefix_filter: list = None,
                         file_exclude_filter: list = None, file_install_tag: list = None,
                         dl_optimizations: bool = False, dl_timeout: int = 10,
                         repair: bool = False, repair_use_latest: bool = False,
                         disable_delta: bool = False, override_delta_manifest: str = '',
                         egl_guid: str = '', preferred_cdn: str = None,
                         no_install: bool = False, ignore_space_req: bool = False,
                         disable_sdl: bool = False, reset_sdl: bool = False, skip_sdl: bool = False,
                         sdl_prompt: Callable[[str, str], List[str]] = list,
                         disable_https: bool = False) -> (DLManager, AnalysisResult, InstalledGame, Game):
        if self.is_installed(app_name):
            igame = self.get_installed_game(app_name)
            platform = igame.platform
            if igame.needs_verification and not repair:
                self.log.info('Game needs to be verified before updating, switching to repair mode...')
                repair = True

        repair_file = None
        if repair:
            repair = True
            no_install = repair_use_latest is False
            repair_file = os.path.join(self.lgd.get_tmp_path(), f'{app_name}.repair')

        if not self.login():
            raise RuntimeError('Login failed! Cannot continue with download process.')

        if file_prefix_filter or file_exclude_filter or file_install_tag:
            no_install = True

        game = self.get_game(app_name, update_meta=True)

        if not game:
            raise RuntimeError(f'Could not find "{app_name}" in list of available games,'
                               f'did you type the name correctly?')

        if game.is_dlc:
            self.log.info('Install candidate is DLC')
            app_name = game.metadata['mainGameItem']['releaseInfo'][0]['appId']
            base_game = self.get_game(app_name)
            # check if base_game is actually installed
            if not self.is_installed(app_name):
                # download mode doesn't care about whether or not something's installed
                if not no_install:
                    raise RuntimeError(f'Base game "{app_name}" is not installed!')
        else:
            base_game = None

        if repair:
            if not self.is_installed(game.app_name):
                raise RuntimeError(f'Game "{game.app_title}" ({game.app_name}) is not installed!')

            if not os.path.exists(repair_file):
                self.log.info('Verifing game...')
                self.verify_game(app_name)
            else:
                self.log.info(f'Using existing repair file: {repair_file}')

        # check if SDL should be disabled
        sdl_enabled = not file_install_tag and not game.is_dlc
        config_tags = self.lgd.config.get(game.app_name, 'install_tags', fallback=None)
        config_disable_sdl = self.lgd.config.getboolean(game.app_name, 'disable_sdl', fallback=False)
        # remove config flag if SDL is reset
        if config_disable_sdl and reset_sdl and not disable_sdl:
            self.lgd.config.remove_option(game.app_name, 'disable_sdl')
        # if config flag is not yet set, set it and remove previous install tags
        elif not config_disable_sdl and disable_sdl:
            self.log.info('Clearing install tags from config and disabling SDL for title.')
            if config_tags:
                self.lgd.config.remove_option(game.app_name, 'install_tags')
                config_tags = None
            self.lgd.config.set(game.app_name, 'disable_sdl', True)
            sdl_enabled = False
        # just disable SDL, but keep config tags that have been manually specified
        elif config_disable_sdl or disable_sdl:
            sdl_enabled = False

        if sdl_enabled and ((sdl_name := get_sdl_appname(game.app_name)) is not None):
            if not self.is_installed(game.app_name) or config_tags is None or reset_sdl:
                sdl_data = self.get_sdl_data(sdl_name, platform=platform)
                if sdl_data:
                    if skip_sdl:
                        file_install_tag = ['']
                        if '__required' in sdl_data:
                            file_install_tag.extend(sdl_data['__required']['tags'])
                    else:
                        file_install_tag = sdl_prompt(sdl_data, game.app_title)
                    self.lgd.config.set(game.app_name, 'install_tags', ','.join(file_install_tag))
                else:
                    self.log.error(f'Unable to get SDL data for {sdl_name}')
            else:
                file_install_tag = config_tags.split(',')
        elif file_install_tag and not game.is_dlc and not no_install:
            config_tags = ','.join(file_install_tag)
            self.log.info(f'Saving install tags for "{game.app_name}" to config: {config_tags}')
            self.lgd.config.set(game.app_name, 'install_tags', config_tags)
        elif not game.is_dlc:
            if config_tags and reset_sdl:
                self.log.info('Clearing install tags from config.')
                self.lgd.config.remove_option(game.app_name, 'install_tags')
            elif config_tags:
                self.log.info(f'Using install tags from config: {config_tags}')
                file_install_tag = config_tags.split(',')

        dlm, analysis, igame = super(LegendaryCore, self).prepare_download(game=game, base_game=base_game, base_path=base_path,
                                                          force=force, max_shm=max_shm,
                                                          max_workers=max_workers, game_folder=game_folder,
                                                          disable_patching=disable_patching,
                                                          override_manifest=override_manifest,
                                                          override_old_manifest=override_old_manifest,
                                                          override_base_url=override_base_url,
                                                          platform=platform,
                                                          file_prefix_filter=file_prefix_filter,
                                                          file_exclude_filter=file_exclude_filter,
                                                          file_install_tag=file_install_tag,
                                                          dl_optimizations=dl_optimizations,
                                                          dl_timeout=dl_timeout,
                                                          repair=repair,
                                                          repair_use_latest=repair_use_latest,
                                                          disable_delta=disable_delta,
                                                          override_delta_manifest=override_delta_manifest,
                                                          preferred_cdn=preferred_cdn,
                                                          status_q=status_q,
                                                          disable_https=disable_https)

        dlm.run_real = DLManager.run_real.__get__(dlm, DLManager)
        # game is either up to date or hasn't changed, so we have nothing to do
        if not analysis.dl_size:
            self.log.info('Download size is 0, the game is either already up to date or has not changed. Exiting...')
            self.clean_post_install(game, igame, repair, repair_file)

            raise RuntimeError('Nothing to do.')

        res = self.check_installation_conditions(analysis=analysis, install=igame, game=game,
                                                 updating=self.is_installed(app_name),
                                                 ignore_space_req=ignore_space_req)

        return dlm, analysis, igame, game, repair, repair_file, res

    def verify_game(self, app_name: str, callback: Callable[[int, int], None] = print):
        if not self.is_installed(app_name):
            self.log.error(f'Game "{app_name}" is not installed')
            return

        self.log.info(f'Loading installed manifest for "{app_name}"')
        igame = self.get_installed_game(app_name)
        manifest_data, _ = self.get_installed_manifest(app_name)
        manifest = self.load_manifest(manifest_data)

        files = sorted(manifest.file_manifest_list.elements,
                       key=lambda a: a.filename.lower())

        # build list of hashes
        file_list = [(f.filename, f.sha_hash.hex()) for f in files]
        total = len(file_list)
        num = 0
        failed = []
        missing = []

        self.log.info(f'Verifying "{igame.title}" version "{manifest.meta.build_version}"')
        repair_file = []
        for result, path, result_hash in validate_files(igame.install_path, file_list):
            if callback:
                num += 1
                callback(num, total)

            if result == VerifyResult.HASH_MATCH:
                repair_file.append(f'{result_hash}:{path}')
                continue
            elif result == VerifyResult.HASH_MISMATCH:
                self.log.error(f'File does not match hash: "{path}"')
                repair_file.append(f'{result_hash}:{path}')
                failed.append(path)
            elif result == VerifyResult.FILE_MISSING:
                self.log.error(f'File is missing: "{path}"')
                missing.append(path)
            else:
                self.log.error(f'Other failure (see log), treating file as missing: "{path}"')
                missing.append(path)

        # always write repair file, even if all match
        if repair_file:
            repair_filename = os.path.join(self.lgd.get_tmp_path(), f'{app_name}.repair')
            with open(repair_filename, 'w') as f:
                f.write('\n'.join(repair_file))
            self.log.debug(f'Written repair file to "{repair_filename}"')

        if not missing and not failed:
            self.log.info('Verification finished successfully.')
        else:
            raise RuntimeError(
                f'Verification failed, {len(failed)} file(s) corrupted, {len(missing)} file(s) are missing.')

    def clean_post_install(self, game: Game, igame: InstalledGame, repair: bool = False, repair_file: str = ''):
        old_igame = self.get_installed_game(game.app_name)
        if old_igame and repair and os.path.exists(repair_file):
            if old_igame.needs_verification:
                old_igame.needs_verification = False
                self.install_game(old_igame)

            self.log.debug('Removing repair file.')
            os.remove(repair_file)

        # check if install tags have changed, if they did; try deleting files that are no longer required.
        if old_igame and old_igame.install_tags != igame.install_tags:
            old_igame.install_tags = igame.install_tags
            self.log.info('Deleting now untagged files.')
            self.uninstall_tag(old_igame)
            self.install_game(old_igame)

    def egl_import(self, app_name):
        __log_error = self.log.error
        __log_fatal = self.log.fatal
        self.log.error = self.__log_exception
        self.log.fatal = self.__log_exception
        super(LegendaryCore, self).egl_import(app_name)
        self.log.error = __log_error
        self.log.fatal = __log_fatal

    def egl_export(self, app_name):
        __log_error = self.log.error
        self.log.error = self.__log_exception
        super(LegendaryCore, self).egl_export(app_name)
        self.log.error = __log_error


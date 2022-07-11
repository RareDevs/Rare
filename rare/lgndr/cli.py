import functools
import os
import logging
import time
from typing import Optional, Union

import legendary.cli
from legendary.cli import logger
from legendary.models.downloading import AnalysisResult, ConditionCheckResult
from legendary.models.game import Game, InstalledGame, VerifyResult
from legendary.utils.lfs import validate_files
from legendary.utils.selective_dl import get_sdl_appname

from .core import LegendaryCore
from .manager import DLManager
from .api_arguments import LgndrInstallGameArgs, LgndrImportGameArgs, LgndrVerifyGameArgs
from .api_exception import LgndrException, LgndrLogHandler
from .api_monkeys import return_exit as exit, get_boolean_choice


class LegendaryCLI(legendary.cli.LegendaryCLI):
    def __init__(self, override_config=None, api_timeout=None):
        self.core = LegendaryCore(override_config, timeout=api_timeout)
        self.logger = logging.getLogger('cli')
        self.logging_queue = None
        self.handler = LgndrLogHandler()
        self.logger.addHandler(self.handler)

    def resolve_aliases(self, name):
        return super(LegendaryCLI, self)._resolve_aliases(name)

    @staticmethod
    def wrapped(func):

        @functools.wraps(func)
        def inner(self, args, *oargs, **kwargs):
            old_exit = legendary.cli.exit
            legendary.cli.exit = exit

            old_choice = legendary.cli.get_boolean_choice
            if hasattr(args, 'get_boolean_choice') and args.get_boolean_choice is not None:
                legendary.cli.get_boolean_choice = args.get_boolean_choice

            try:
                return func(self, args, *oargs, **kwargs)
            except LgndrException as ret:
                print(f'Caught exception in wrapped function {ret.message}')
                raise ret
            finally:
                legendary.cli.get_boolean_choice = old_choice
                legendary.cli.exit = old_exit

        return inner

    @wrapped
    def install_game(self, args: LgndrInstallGameArgs) -> (DLManager, AnalysisResult, InstalledGame, Game, bool, Optional[str], ConditionCheckResult):
        args.app_name = self._resolve_aliases(args.app_name)
        if self.core.is_installed(args.app_name):
            igame = self.core.get_installed_game(args.app_name)
            args.platform = igame.platform
            if igame.needs_verification and not args.repair_mode:
                logger.info('Game needs to be verified before updating, switching to repair mode...')
                args.repair_mode = True

        repair_file = None
        # Rare: The 'args.no_install' flags is set externally from the InstallDialog
        if args.repair_mode:
            args.repair_mode = True
            args.no_install = args.repair_and_update is False
            repair_file = os.path.join(self.core.lgd.get_tmp_path(), f'{args.app_name}.repair')

        if args.file_prefix or args.file_exclude_prefix:
            args.no_install = True

        game = self.core.get_game(args.app_name, update_meta=True, platform=args.platform)

        if not game:
            logger.error(f'Could not find "{args.app_name}" in list of available games, '
                         f'did you type the name correctly?')

        if args.platform not in game.asset_infos:
            if not args.no_install:
                if self.core.lgd.config.getboolean('Legendary', 'install_platform_fallback', fallback=True):
                    logger.warning(f'App has no asset for platform "{args.platform}", falling back to "Windows".')
                    args.platform = 'Windows'
                else:
                    logger.error(f'No app asset found for platform "{args.platform}", run '
                                 f'"legendary info --platform {args.platform}" and make '
                                 f'sure the app is available for the specified platform.')
                    return
            else:
                logger.warning(f'No asset found for platform "{args.platform}", '
                               f'trying anyway since --no-install is set.')

        if game.is_dlc:
            logger.info('Install candidate is DLC')
            app_name = game.metadata['mainGameItem']['releaseInfo'][0]['appId']
            base_game = self.core.get_game(app_name)
            # check if base_game is actually installed
            if not self.core.is_installed(app_name):
                # download mode doesn't care about whether something's installed
                if not args.no_install:
                    logger.fatal(f'Base game "{app_name}" is not installed!')
        else:
            base_game = None

        if args.repair_mode:
            if not self.core.is_installed(game.app_name):
                logger.error(f'Game "{game.app_title}" ({game.app_name}) is not installed!')

            if not os.path.exists(repair_file):
                logger.info('Game has not been verified yet.')
                if not args.yes:
                    if not get_boolean_choice(f'Verify "{game.app_name}" now ("no" will abort repair)?'):
                        return
                try:
                    self.verify_game(args, print_command=False, repair_mode=True, repair_online=args.repair_and_update)
                except ValueError:
                    logger.error('To repair a game with a missing manifest you must run the command with '
                                 '"--repair-and-update". However this will redownload any file that does '
                                 'not match the current hash in its entirety.')
                    return
            else:
                logger.info(f'Using existing repair file: {repair_file}')

        # check if SDL should be disabled
        sdl_enabled = not args.install_tag and not game.is_dlc
        config_tags = self.core.lgd.config.get(game.app_name, 'install_tags', fallback=None)
        config_disable_sdl = self.core.lgd.config.getboolean(game.app_name, 'disable_sdl', fallback=False)
        # remove config flag if SDL is reset
        if config_disable_sdl and args.reset_sdl and not args.disable_sdl:
            self.core.lgd.config.remove_option(game.app_name, 'disable_sdl')
        # if config flag is not yet set, set it and remove previous install tags
        elif not config_disable_sdl and args.disable_sdl:
            logger.info('Clearing install tags from config and disabling SDL for title.')
            if config_tags:
                self.core.lgd.config.remove_option(game.app_name, 'install_tags')
                config_tags = None
            self.core.lgd.config.set(game.app_name, 'disable_sdl', True)
            sdl_enabled = False
        # just disable SDL, but keep config tags that have been manually specified
        elif config_disable_sdl or args.disable_sdl:
            sdl_enabled = False

        if sdl_enabled and ((sdl_name := get_sdl_appname(game.app_name)) is not None):
            if not self.core.is_installed(game.app_name) or config_tags is None or args.reset_sdl:
                sdl_data = self.core.get_sdl_data(sdl_name, platform=args.platform)
                if sdl_data:
                    if args.skip_sdl:
                        args.install_tag = ['']
                        if '__required' in sdl_data:
                            args.install_tag.extend(sdl_data['__required']['tags'])
                    else:
                        args.install_tag = args.sdl_prompt(sdl_data, game.app_title)
                    self.core.lgd.config.set(game.app_name, 'install_tags', ','.join(args.install_tag))
                else:
                    logger.error(f'Unable to get SDL data for {sdl_name}')
            else:
                args.install_tag = config_tags.split(',')
        elif args.install_tag and not game.is_dlc and not args.no_install:
            config_tags = ','.join(args.install_tag)
            logger.info(f'Saving install tags for "{game.app_name}" to config: {config_tags}')
            self.core.lgd.config.set(game.app_name, 'install_tags', config_tags)
        elif not game.is_dlc:
            if config_tags and args.reset_sdl:
                logger.info('Clearing install tags from config.')
                self.core.lgd.config.remove_option(game.app_name, 'install_tags')
            elif config_tags:
                logger.info(f'Using install tags from config: {config_tags}')
                args.install_tag = config_tags.split(',')

        logger.info(f'Preparing download for "{game.app_title}" ({game.app_name})...')
        # todo use status queue to print progress from CLI
        # This has become a little ridiculous hasn't it?
        dlm, analysis, igame = self.core.prepare_download(game=game, base_game=base_game, base_path=args.base_path,
                                                          status_q=args.status_q,
                                                          force=args.force, max_shm=args.shared_memory,
                                                          max_workers=args.max_workers, game_folder=args.game_folder,
                                                          disable_patching=args.disable_patching,
                                                          override_manifest=args.override_manifest,
                                                          override_old_manifest=args.override_old_manifest,
                                                          override_base_url=args.override_base_url,
                                                          platform=args.platform,
                                                          file_prefix_filter=args.file_prefix,
                                                          file_exclude_filter=args.file_exclude_prefix,
                                                          file_install_tag=args.install_tag,
                                                          dl_optimizations=args.order_opt,
                                                          dl_timeout=args.dl_timeout,
                                                          repair=args.repair_mode,
                                                          repair_use_latest=args.repair_and_update,
                                                          disable_delta=args.disable_delta,
                                                          override_delta_manifest=args.override_delta_manifest,
                                                          preferred_cdn=args.preferred_cdn,
                                                          disable_https=args.disable_https)

        # game is either up-to-date or hasn't changed, so we have nothing to do
        if not analysis.dl_size:
            logger.info('Download size is 0, the game is either already up to date or has not changed. Exiting...')
            self.clean_post_install(game, igame, args.repair_mode, repair_file)

            logger.error('Nothing to do.')

        res = self.core.check_installation_conditions(analysis=analysis, install=igame, game=game,
                                                      updating=self.core.is_installed(args.app_name),
                                                      ignore_space_req=args.ignore_space)

        return dlm, analysis, igame, game, args.repair_mode, repair_file, res

    def clean_post_install(self, game: Game, igame: InstalledGame, repair: bool = False, repair_file: str = ''):
        old_igame = self.core.get_installed_game(game.app_name)
        if old_igame and repair and os.path.exists(repair_file):
            if old_igame.needs_verification:
                old_igame.needs_verification = False
                self.core.install_game(old_igame)

            logger.debug('Removing repair file.')
            os.remove(repair_file)

        # check if install tags have changed, if they did; try deleting files that are no longer required.
        if old_igame and old_igame.install_tags != igame.install_tags:
            old_igame.install_tags = igame.install_tags
            logger.info('Deleting now untagged files.')
            self.core.uninstall_tag(old_igame)
            self.core.install_game(old_igame)

    def _handle_postinstall(self, postinstall, igame, yes=False):
        super(LegendaryCLI, self)._handle_postinstall(postinstall, igame, yes)

    @wrapped
    def uninstall_game(self, args):
        super(LegendaryCLI, self).uninstall_game(args)

    @wrapped
    def verify_game(self, args: Union[LgndrVerifyGameArgs, LgndrInstallGameArgs], print_command=True, repair_mode=False, repair_online=False):
        args.app_name = self._resolve_aliases(args.app_name)
        if not self.core.is_installed(args.app_name):
            logger.error(f'Game "{args.app_name}" is not installed')
            return

        logger.info(f'Loading installed manifest for "{args.app_name}"')
        igame = self.core.get_installed_game(args.app_name)
        if not os.path.exists(igame.install_path):
            logger.error(f'Install path "{igame.install_path}" does not exist, make sure all necessary mounts '
                         f'are available. If you previously deleted the game folder without uninstalling, run '
                         f'"legendary uninstall -y {igame.app_name}" and reinstall from scratch.')
            return

        manifest_data, _ = self.core.get_installed_manifest(args.app_name)
        if manifest_data is None:
            if repair_mode:
                if not repair_online:
                    logger.critical('No manifest could be loaded, the manifest file may be missing!')
                    raise ValueError('Local manifest is missing')

                logger.warning('No manifest could be loaded, the file may be missing. Downloading the latest manifest.')
                game = self.core.get_game(args.app_name, platform=igame.platform)
                manifest_data, _ = self.core.get_cdn_manifest(game, igame.platform)
                # Rare: Save the manifest if we downloaded it because it was missing
                self.core.lgd.save_manifest(game.app_name, manifest_data,
                                            version=self.core.load_manifest(manifest_data).meta.build_version,
                                            platform=igame.platform)
            else:
                logger.critical(f'Manifest appears to be missing! To repair, run "legendary repair '
                                f'{args.app_name} --repair-and-update", this will however redownload all files '
                                f'that do not match the latest manifest in their entirety.')
                return

        manifest = self.core.load_manifest(manifest_data)

        files = sorted(manifest.file_manifest_list.elements,
                       key=lambda a: a.filename.lower())

        # build list of hashes
        if config_tags := self.core.lgd.config.get(args.app_name, 'install_tags', fallback=None):
            install_tags = set(i.strip() for i in config_tags.split(','))
            file_list = [
                (f.filename, f.sha_hash.hex())
                for f in files
                if any(it in install_tags for it in f.install_tags) or not f.install_tags
            ]
        else:
            file_list = [(f.filename, f.sha_hash.hex()) for f in files]

        total = len(file_list)
        total_size = sum(manifest.file_manifest_list.get_file_by_path(fm[0]).file_size
                         for fm in file_list)
        num = processed = last_processed = 0
        speed = 0.0
        percentage = 0.0
        failed = []
        missing = []

        last_update = time.time()

        logger.info(f'Verifying "{igame.title}" version "{manifest.meta.build_version}"')
        repair_file = []
        for result, path, result_hash, bytes_read in validate_files(igame.install_path, file_list):
            processed += bytes_read
            percentage = (processed / total_size) * 100.0
            num += 1

            if (delta := ((current_time := time.time()) - last_update)) > 1 or (not last_processed and delta > 1):
                last_update = current_time
                speed = (processed - last_processed) / 1024 / 1024 / delta
                last_processed = processed

            if args.verify_stdout:
                args.verify_stdout(num, total, percentage, speed)

            if result == VerifyResult.HASH_MATCH:
                repair_file.append(f'{result_hash}:{path}')
                continue
            elif result == VerifyResult.HASH_MISMATCH:
                logger.info(f'File does not match hash: "{path}"')
                repair_file.append(f'{result_hash}:{path}')
                failed.append(path)
            elif result == VerifyResult.FILE_MISSING:
                logger.info(f'File is missing: "{path}"')
                missing.append(path)
            else:
                logger.info(f'Other failure (see log), treating file as missing: "{path}"')
                missing.append(path)

        if args.verify_stdout:
            args.verify_stdout(num, total, percentage, speed)

        # always write repair file, even if all match
        if repair_file:
            repair_filename = os.path.join(self.core.lgd.get_tmp_path(), f'{args.app_name}.repair')
            with open(repair_filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(repair_file))
            logger.debug(f'Written repair file to "{repair_filename}"')

        if not missing and not failed:
            logger.info('Verification finished successfully.')
            return True, 0, 0
        else:
            logger.warning(f'Verification failed, {len(failed)} file(s) corrupted, {len(missing)} file(s) are missing.')
            if print_command:
                logger.info(f'Run "legendary repair {args.app_name}" to repair your game installation.')
            return False, len(failed), len(missing)

    @wrapped
    def import_game(self, args: LgndrImportGameArgs):
        super(LegendaryCLI, self).import_game(args)

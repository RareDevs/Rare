import logging
import os
import queue
import subprocess
import time
from typing import Optional, Union, Tuple

from legendary.cli import LegendaryCLI as LegendaryCLIReal
from legendary.models.downloading import AnalysisResult, ConditionCheckResult
from legendary.models.game import Game, InstalledGame, VerifyResult
from legendary.lfs.utils import validate_files
from legendary.utils.selective_dl import get_sdl_appname

from rare.lgndr.core import LegendaryCore
from rare.lgndr.downloader.mp.manager import DLManager
from rare.lgndr.glue.arguments import (
    LgndrInstallGameArgs,
    LgndrImportGameArgs,
    LgndrVerifyGameArgs,
    LgndrUninstallGameArgs,
    LgndrInstallGameRealArgs,
    LgndrInstallGameRealRet,
)
from rare.lgndr.glue.monkeys import LgndrIndirectStatus, LgndrIndirectLogger


# fmt: off
class LegendaryCLI(LegendaryCLIReal):

    # noinspection PyMissingConstructor
    def __init__(self, core: LegendaryCore):
        self.core = core
        self.logger = logging.getLogger('Cli')
        self.logging_queue = None
        self.ql = self.setup_threaded_logging()

    def __del__(self):
        self.ql.stop()

    def resolve_aliases(self, name):
        return super(LegendaryCLI, self)._resolve_aliases(name)

    def install_game(self, args: LgndrInstallGameArgs) -> Optional[Tuple[DLManager, AnalysisResult, InstalledGame, Game, bool, Optional[str], ConditionCheckResult]]:
        # Override logger for the local context to use message as part of the indirect return value
        logger = LgndrIndirectLogger(args.indirect_status, self.logger)
        get_boolean_choice = args.get_boolean_choice
        sdl_prompt = args.sdl_prompt

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

        # Rare: Rare is already logged in

        if args.file_prefix or args.file_exclude_prefix:
            args.no_install = True

        # Rare: Rare runs updates on already installed games only

        game = self.core.get_game(args.app_name, update_meta=True, platform=args.platform)

        if not game:
            logger.error(f'Could not find "{args.app_name}" in list of available games, '
                         f'did you type the name correctly?')
            return

        # Rare: Rare checks this before calling 'install_game'

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
                    return
        else:
            base_game = None

        if args.repair_mode:
            if not self.core.is_installed(game.app_name):
                logger.error(f'Game "{game.app_title}" ({game.app_name}) is not installed!')
                return

            if not os.path.exists(repair_file):
                logger.info('Game has not been verified yet.')
                # Rare: we do not want to verify while preparing the download in the InstallDialog
                # Rare: we handle it differently through the GameInfo tab
                logger.error('Game has not been verified yet.')
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
                        args.install_tag = sdl_prompt(sdl_data, game.app_title)
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
        if not analysis.dl_size and not game.is_dlc:
            logger.info('Download size is 0, the game is either already up to date or has not changed. Exiting...')
            self.install_game_cleanup(game, igame, args.repair_mode, repair_file)
            # return
            # Rare: Return what we know about the download to queue a 0 size DLC
            res = self.core.check_installation_conditions(analysis=analysis, install=igame, game=game,
                                                          updating=self.core.is_installed(args.app_name),
                                                          ignore_space_req=args.ignore_space)
            return dlm, analysis, igame, game, args.repair_mode, repair_file, res

        res = self.core.check_installation_conditions(analysis=analysis, install=igame, game=game,
                                                      updating=self.core.is_installed(args.app_name),
                                                      ignore_space_req=args.ignore_space)

        return dlm, analysis, igame, game, args.repair_mode, repair_file, res

    # Rare: This is currently handled in DownloadThread, this is a trial
    def install_game_real(self, args: LgndrInstallGameRealArgs, dlm: DLManager, game: Game, igame: InstalledGame) -> LgndrInstallGameRealRet:
        # Override logger for the local context to use message as part of the indirect return value
        logger = LgndrIndirectLogger(args.indirect_status, self.logger)
        ret = LgndrInstallGameRealRet(game.app_name)

        start_t = time.time()

        try:
            # set up logging stuff (should be moved somewhere else later)
            dlm.logging_queue = self.logging_queue
            dlm.proc_debug = args.dlm_debug

            dlm.start()
            while dlm.is_alive():
                try:
                    args.ui_update(dlm.status_queue.get(timeout=1.0))
                except queue.Empty:
                    pass
                if args.dlm_signals.update:
                    try:
                        dlm.signals_queue.put(args.dlm_signals, block=False, timeout=1.0)
                    except queue.Full:
                        pass
                time.sleep(dlm.update_interval / 10)
            dlm.join()
        except Exception as e:
            end_t = time.time()
            logger.info(f'Installation failed after {end_t - start_t:.02f} seconds.')
            logger.warning(f'The following exception occurred while waiting for the downloader to finish: {e!r}. '
                           f'Try restarting the process, the resume file will be used to start where it failed. '
                           f'If it continues to fail please open an issue on GitHub.')
            ret.ret_code = ret.ReturnCode.ERROR
            ret.message = f"{e!r}"
            return ret
        else:
            end_t = time.time()
            if args.dlm_signals.kill is True:
                logger.info(f"Download stopped after {end_t - start_t:.02f} seconds.")
                ret.exit_code = ret.ReturnCode.STOPPED
                return ret
            logger.info(f"Download finished in {end_t - start_t:.02f} seconds.")
            if not args.no_install:
                # Allow setting savegame directory at install time so sync-saves will work immediately
                if (game.supports_cloud_saves or game.supports_mac_cloud_saves) and args.save_path:
                    igame.save_path = args.save_path

                postinstall = self.core.install_game(igame)
                if postinstall:
                    self._handle_postinstall(postinstall, igame, skip_prereqs=args.yes, choice=args.install_prereqs)

                dlcs = self.core.get_dlc_for_game(game.app_name)
                if dlcs and not args.skip_dlcs:
                    for dlc in dlcs:
                        ret.dlcs.append(
                            {
                                "app_name": dlc.app_name,
                                "app_title": dlc.app_title,
                                "app_version": dlc.app_version(args.platform)
                            }
                        )

                    # Rare: We do not install DLCs automatically, we offer to do so through our downloads tab

                if (game.supports_cloud_saves or game.supports_mac_cloud_saves) and not game.is_dlc:
                    # todo option to automatically download saves after the installation
                    #  args does not have the required attributes for sync_saves in here,
                    #  not sure how to solve that elegantly.
                    logger.info(f'This game supports cloud saves, syncing is handled by the "sync-saves" command. '
                                f'To download saves for this game run "legendary sync-saves {args.app_name}"')
                    ret.sync_saves = True

                # show tip again after installation finishes so users hopefully actually see it
                if tip_url := self.core.get_game_tip(igame.app_name):
                    ret.tip_url = tip_url

            self.install_game_cleanup(game, igame, args.repair_mode, args.repair_file)

            logger.info(f'Finished installation process in {end_t - start_t:.02f} seconds.')

            return ret

    def install_game_cleanup(self, game: Game, igame: InstalledGame, repair_mode: bool = False, repair_file: str = '') -> None:
        # Override logger for the local context to use message as part of the indirect return value
        logger = LgndrIndirectLogger(LgndrIndirectStatus(), self.logger)

        old_igame = self.core.get_installed_game(game.app_name)
        if old_igame and repair_mode and os.path.exists(repair_file):
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

        if old_igame.install_tags:
            self.core.lgd.config.set(game.app_name, 'install_tags', ','.join(old_igame.install_tags))
            self.core.lgd.save_config()

    def _handle_postinstall(self, postinstall, igame, skip_prereqs=False, choice=True):
        # Override logger for the local context to use message as part of the indirect return value
        logger = LgndrIndirectLogger(LgndrIndirectStatus(), self.logger)
        # noinspection PyShadowingBuiltins
        def print(x): self.logger.info(x) if x else None
        # noinspection PyShadowingBuiltins
        def input(x): return 'y' if choice else 'n'

        print('\nThis game lists the following prerequisites to be installed:')
        print(f'- {postinstall["name"]}: {" ".join((postinstall["path"], postinstall["args"]))}')
        print('')

        if os.name == 'nt':
            if skip_prereqs:
                c = 'n'  # we don't want to launch anything, just silent install.
            else:
                choice = input('Do you wish to install the prerequisites? ([y]es, [n]o, [i]gnore): ')
                c = choice.lower()[0]
                print('')

            if c == 'i':  # just set it to installed
                logger.info('Marking prerequisites as installed...')
                self.core.prereq_installed(igame.app_name)
            elif c == 'y':  # set to installed and launch installation
                logger.info('Launching prerequisite executable..')
                self.core.prereq_installed(igame.app_name)
                req_path, req_exec = os.path.split(postinstall['path'])
                work_dir = os.path.join(igame.install_path, req_path)
                fullpath = os.path.join(work_dir, req_exec)
                try:
                    p = subprocess.Popen([fullpath, postinstall['args']], cwd=work_dir, shell=True)
                    p.wait()
                except Exception as e:
                    logger.error(f'Failed to run prereq executable with: {e!r}')
        else:
            logger.info('Automatic installation not available on Linux.')

    def uninstall_game(self, args: LgndrUninstallGameArgs) -> None:
        # Override logger for the local context to use message as part of the indirect return value
        logger = LgndrIndirectLogger(args.indirect_status, self.logger, logging.WARNING)
        get_boolean_choice = args.get_boolean_choice

        args.app_name = self._resolve_aliases(args.app_name)
        igame = self.core.get_installed_game(args.app_name)
        if not igame:
            logger.error(f'Game {args.app_name} not installed, cannot uninstall!')
            return

        if not args.yes:
            if not get_boolean_choice(f'Do you wish to uninstall "{igame.title}"?', default=False):
                return

        try:
            if not igame.is_dlc:
                # Remove DLC first so directory is empty when game uninstall runs
                dlcs = self.core.get_dlc_for_game(igame.app_name)
                for dlc in dlcs:
                    if (idlc := self.core.get_installed_game(dlc.app_name)) is not None:
                        logger.info(f'Uninstalling DLC "{dlc.app_name}"...')
                        self.core.uninstall_game(idlc, delete_files=not args.keep_files)

            logger.info(f'Removing "{igame.title}" from "{igame.install_path}"...')
            self.core.uninstall_game(igame, delete_files=not args.keep_files,
                                     delete_root_directory=not igame.is_dlc)
            logger.info('Game has been uninstalled.')
            return
        except Exception as e:
            logger.warning(f'Removing game failed: {e!r}, please remove {igame.install_path} manually.')
            return

    def verify_game(self, args: Union[LgndrVerifyGameArgs, LgndrInstallGameArgs], print_command=True, repair_mode=False, repair_online=False) -> Optional[Tuple[int, int]]:
        # Override logger for the local context to use message as part of the indirect return value
        logger = LgndrIndirectLogger(args.indirect_status, self.logger)

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
        if (config_tags := self.core.lgd.config.get(args.app_name, 'install_tags', fallback=None)) is not None:
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

            if (delta := ((current_time := time.time()) - last_update)) > 1:
                last_update = current_time
                speed = (processed - last_processed) / 1024 / 1024 / delta
                last_processed = processed

            if args.verify_stdout:
                args.verify_stdout(num, total, percentage, speed)

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
            return 0, 0
        else:
            logger.error(f'Verification failed, {len(failed)} file(s) corrupted, {len(missing)} file(s) are missing.')
            if print_command:
                logger.info(f'Run "legendary repair {args.app_name}" to repair your game installation.')
            return len(failed), len(missing)

    def import_game(self, args: LgndrImportGameArgs) -> None:
        # Override logger for the local context to use message as part of the indirect return value
        logger = LgndrIndirectLogger(args.indirect_status, self.logger)
        get_boolean_choice = args.get_boolean_choice

        # make sure path is absolute
        args.app_path = os.path.abspath(args.app_path)
        args.app_name = self._resolve_aliases(args.app_name)

        if not os.path.exists(args.app_path):
            logger.error(f'Specified path "{args.app_path}" does not exist!')
            return

        if self.core.is_installed(args.app_name):
            logger.error('Game is already installed!')
            return

        if not self.core.login():
            logger.error('Log in failed!')
            return

        # do some basic checks
        game = self.core.get_game(args.app_name, update_meta=True, platform=args.platform)
        if not game:
            logger.fatal(f'Did not find game "{args.app_name}" on account.')
            return

        if game.is_dlc:
            release_info = game.metadata.get('mainGameItem', {}).get('releaseInfo')
            if release_info:
                main_game_appname = release_info[0]['appId']
                main_game_title = game.metadata['mainGameItem']['title']
                if not self.core.is_installed(main_game_appname):
                    logger.error(f'Import candidate is DLC but base game "{main_game_title}" '
                                 f'(App name: "{main_game_appname}") is not installed!')
                    return
            else:
                logger.fatal(f'Unable to get base game information for DLC, cannot continue.')
                return

        # get everything needed for import from core, then run additional checks.
        manifest, igame = self.core.import_game(game, args.app_path, platform=args.platform)
        exe_path = os.path.join(args.app_path, manifest.meta.launch_exe.lstrip('/'))
        # check if most files at least exist or if user might have specified the wrong directory
        total = len(manifest.file_manifest_list.elements)
        found = sum(os.path.exists(os.path.join(args.app_path, f.filename))
                    for f in manifest.file_manifest_list.elements)
        ratio = found / total

        if not found:
            logger.error(f'No files belonging to {"DLC" if game.is_dlc else "Game"} "{game.app_title}" '
                         f'({game.app_name}) found in the specified location, please verify that the path is correct.')
            if not game.is_dlc:
                # check if game folder is in path, suggest alternative
                folder = game.metadata.get('customAttributes', {}).get('FolderName', {}).get('value', game.app_name)
                if folder and folder not in args.app_path:
                    new_path = os.path.join(args.app_path, folder)
                    logger.info(f'Did you mean "{new_path}"?')
            return

        if not game.is_dlc and not os.path.exists(exe_path) and not args.disable_check:
            logger.error(f'Game executable could not be found at "{exe_path}", '
                         f'please verify that the specified path is correct.')
            return

        if ratio < 0.95:
            logger.warning('Some files are missing from the game installation, install may not '
                           'match latest Epic Games Store version or might be corrupted.')
        else:
            logger.info(f'{"DLC" if game.is_dlc else "Game"} install appears to be complete.')

        self.core.install_game(igame)
        if igame.needs_verification:
            logger.info(f'NOTE: The {"DLC" if game.is_dlc else "Game"} installation will have to be '
                        f'verified before it can be updated with legendary.')
            logger.info(f'Run "legendary repair {args.app_name}" to do so.')
        else:
            logger.info(f'Installation had Epic Games Launcher metadata for version "{igame.version}", '
                        f'verification will not be required.')

        # check for importable DLC
        if not args.skip_dlcs:
            dlcs = self.core.get_dlc_for_game(game.app_name)
            if dlcs:
                logger.info(f'Found {len(dlcs)} items of DLC that could be imported.')
                import_dlc = True
                if not args.yes and not args.with_dlcs:
                    if not get_boolean_choice(f'Do you wish to automatically attempt to import all DLCs?'):
                        import_dlc = False

                if import_dlc:
                    for dlc in dlcs:
                        args.app_name = dlc.app_name
                        self.import_game(args)

        logger.info(f'{"DLC" if game.is_dlc else "Game"} "{game.app_title}" has been imported.')
        return

    def move(self, args):
        # Override logger for the local context to use message as part of the indirect return value
        logger = LgndrIndirectLogger(args.indirect_status, self.logger)

        app_name = self._resolve_aliases(args.app_name)
        igame = self.core.get_installed_game(app_name, skip_sync=True)
        if not igame:
            logger.error(f'No installed game found for "{app_name}"')
            return

        old_base, game_folder = os.path.split(igame.install_path.replace('\\', '/'))
        new_path = os.path.join(args.new_path, game_folder)
        logger.info(f'Moving "{game_folder}" from "{old_base}" to "{args.new_path}"')

        if not args.skip_move:
            try:
                if not os.path.exists(args.new_path):
                    os.makedirs(args.new_path)

                os.rename(igame.install_path, new_path)
            except Exception as e:
                # pylint: disable=E1101
                if isinstance(e, OSError) and e.errno == 18:
                    logger.error(f'Moving to a different drive is not supported. Move the folder manually to '
                                 f'"{new_path}" and run "legendary move {app_name} "{args.new_path}" --skip-move"')
                elif isinstance(e, FileExistsError):
                    logger.error(f'The target path already contains a folder called "{game_folder}", '
                                 f'please remove or rename it first.')
                else:
                    logger.error(f'Moving failed with unknown error {e!r}.')
                    logger.info(f'Try moving the folder manually to "{new_path}" and running '
                                f'"legendary move {app_name} "{args.new_path}" --skip-move"')
                return
        else:
            logger.info(f'Not moving, just rewriting legendary metadata...')

        igame.install_path = new_path
        self.core.install_game(igame)
        logger.info('Finished.')

# fmt: on

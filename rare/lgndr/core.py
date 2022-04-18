import os

from multiprocessing import Queue
from typing import Callable

from legendary.utils.lfs import clean_filename, validate_files
from legendary.models.downloading import AnalysisResult
from legendary.models.game import *
from legendary.utils.game_workarounds import is_opt_enabled
from legendary.utils.selective_dl import get_sdl_appname
from legendary.utils.manifests import combine_manifests

from legendary.core import LegendaryCore as LegendaryCoreReal
from .manager import DLManager


class LegendaryCore(LegendaryCoreReal):

    def prepare_download(self, app_name: str, base_path: str = '', no_install: bool = False,
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
                         disable_https: bool = False, ignore_space_req: bool = False, reset_sdl: bool = False,
                         sdl_prompt: Callable[[str, str], List[str]] = list) \
            -> (DLManager, AnalysisResult, Game, InstalledGame):
        if self.is_installed(app_name):
            igame = self.get_installed_game(app_name)
            platform = igame.platform
            if igame.needs_verification and not repair:
                self.log.info('Game needs to be verified before updating, switching to repair mode...')
                repair = True

        repair_file = ''
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

        # Workaround for Cyberpunk 2077 preload
        if not file_install_tag and not game.is_dlc and ((sdl_name := get_sdl_appname(game.app_name)) is not None):
            config_tags = self.lgd.config.get(game.app_name, 'install_tags', fallback=None)
            if not self.is_installed(game.app_name) or config_tags is None or reset_sdl:
                file_install_tag = sdl_prompt(sdl_name, game.app_title)
                if game.app_name not in self.lgd.config:
                    self.lgd.config[game.app_name] = dict()
                self.lgd.config.set(game.app_name, 'install_tags', ','.join(file_install_tag))
            else:
                file_install_tag = config_tags.split(',')

        # load old manifest
        old_manifest = None

        # load old manifest if we have one
        if override_old_manifest:
            self.log.info(f'Overriding old manifest with "{override_old_manifest}"')
            old_bytes, _ = self.get_uri_manifest(override_old_manifest)
            old_manifest = self.load_manifest(old_bytes)
        elif not disable_patching and not force and self.is_installed(game.app_name):
            old_bytes, _base_urls = self.get_installed_manifest(game.app_name)
            if _base_urls and not game.base_urls:
                game.base_urls = _base_urls

            if not old_bytes:
                self.log.error(f'Could not load old manifest, patching will not work!')
            else:
                old_manifest = self.load_manifest(old_bytes)

        base_urls = game.base_urls

        # The EGS client uses plaintext HTTP by default for the purposes of enabling simple DNS based
        # CDN redirection to a (local) cache. In Legendary this will be a config option.
        disable_https = disable_https or self.lgd.config.getboolean('Legendary', 'disable_https', fallback=False)

        if override_manifest:
            self.log.info(f'Overriding manifest with "{override_manifest}"')
            new_manifest_data, _base_urls = self.get_uri_manifest(override_manifest)
            # if override manifest has a base URL use that instead
            if _base_urls:
                base_urls = _base_urls
        else:
            new_manifest_data, base_urls = self.get_cdn_manifest(game, platform, disable_https=disable_https)
            # overwrite base urls in metadata with current ones to avoid using old/dead CDNs
            game.base_urls = base_urls
            # save base urls to game metadata
            self.lgd.set_game_meta(game.app_name, game)

        self.log.info('Parsing game manifest...')
        new_manifest = self.load_manifest(new_manifest_data)
        self.log.debug(f'Base urls: {base_urls}')
        # save manifest with version name as well for testing/downgrading/etc.
        self.lgd.save_manifest(game.app_name, new_manifest_data,
                               version=new_manifest.meta.build_version,
                               platform=platform)

        # check if we should use a delta manifest or not
        disable_delta = disable_delta or ((override_old_manifest or override_manifest) and not override_delta_manifest)
        if old_manifest and new_manifest:
            disable_delta = disable_delta or (old_manifest.meta.build_id == new_manifest.meta.build_id)
        if old_manifest and new_manifest and not disable_delta:
            if override_delta_manifest:
                self.log.info(f'Overriding delta manifest with "{override_delta_manifest}"')
                delta_manifest_data, _ = self.get_uri_manifest(override_delta_manifest)
            else:
                delta_manifest_data = self.get_delta_manifest(base_urls[0],
                                                              old_manifest.meta.build_id,
                                                              new_manifest.meta.build_id)
            if delta_manifest_data:
                delta_manifest = self.load_manifest(delta_manifest_data)
                self.log.info(f'Using optimized delta manifest to upgrade from build '
                              f'"{old_manifest.meta.build_id}" to '
                              f'"{new_manifest.meta.build_id}"...')
                combine_manifests(new_manifest, delta_manifest)
            else:
                self.log.debug(f'No Delta manifest received from CDN.')

        # reuse existing installation's directory
        if igame := self.get_installed_game(base_game.app_name if base_game else game.app_name):
            install_path = igame.install_path
            # make sure to re-use the epic guid we assigned on first install
            if not game.is_dlc and igame.egl_guid:
                egl_guid = igame.egl_guid
        else:
            if not game_folder:
                if game.is_dlc:
                    game_folder = base_game.metadata.get('customAttributes', {}). \
                        get('FolderName', {}).get('value', base_game.app_name)
                else:
                    game_folder = game.metadata.get('customAttributes', {}). \
                        get('FolderName', {}).get('value', game.app_name)

            if not base_path:
                base_path = self.get_default_install_dir(platform=platform)

                if platform == 'Mac':
                    # if we're on mac and the path to the binary does not start with <something>.app,
                    # treat it as if it were a Windows game instead and install it to the default folder.
                    if '.app' not in new_manifest.meta.launch_exe.partition('/')[0].lower():
                        base_path = self.get_default_install_dir(platform='Windows')
                    else:
                        # If it is a .app omit the game folder
                        game_folder = ''

            # make sure base directory actually exists (but do not create game dir)
            if not os.path.exists(base_path):
                self.log.info(f'"{base_path}" does not exist, creating...')
                os.makedirs(base_path)

            install_path = os.path.normpath(os.path.join(base_path, game_folder))

        # check for write access on the install path or its parent directory if it doesn't exist yet
        base_path = os.path.dirname(install_path)
        if os.path.exists(install_path) and not os.access(install_path, os.W_OK):
            raise PermissionError(f'No write access to "{install_path}"')
        elif not os.access(base_path, os.W_OK):
            raise PermissionError(f'No write access to "{base_path}"')

        self.log.info(f'Install path: {install_path}')

        if repair:
            if not repair_use_latest and old_manifest:
                # use installed manifest for repairs instead of updating
                new_manifest = old_manifest
                old_manifest = None

            filename = clean_filename(f'{game.app_name}.repair')
            resume_file = os.path.join(self.lgd.get_tmp_path(), filename)
            force = False
        elif not force:
            filename = clean_filename(f'{game.app_name}.resume')
            resume_file = os.path.join(self.lgd.get_tmp_path(), filename)
        else:
            resume_file = None

        # Use user-specified base URL or preferred CDN first, otherwise fall back to
        # EGS's behaviour of just selecting the first CDN in the list.
        base_url = None
        if override_base_url:
            self.log.info(f'Overriding base URL with "{override_base_url}"')
            base_url = override_base_url
        elif preferred_cdn or (preferred_cdn := self.lgd.config.get('Legendary', 'preferred_cdn', fallback=None)):
            for url in base_urls:
                if preferred_cdn in url:
                    base_url = url
                    break
            else:
                self.log.warning(f'Preferred CDN "{preferred_cdn}" unavailable, using default selection.')
        # Use first, fail if none known
        if not base_url:
            if not base_urls:
                raise ValueError('No base URLs found, please try again.')
            base_url = base_urls[0]

        if disable_https:
            base_url = base_url.replace('https://', 'http://')

        self.log.debug(f'Using base URL: {base_url}')
        scheme, cdn_host = base_url.split('/')[0:3:2]
        self.log.info(f'Selected CDN: {cdn_host} ({scheme.strip(":")})')

        if not max_shm:
            max_shm = self.lgd.config.getint('Legendary', 'max_memory', fallback=2048)

        if dl_optimizations or is_opt_enabled(game.app_name, new_manifest.meta.build_version):
            self.log.info('Download order optimizations are enabled.')
            process_opt = True
        else:
            process_opt = False

        if not max_workers:
            max_workers = self.lgd.config.getint('Legendary', 'max_workers', fallback=0)

        dlm = DLManager(install_path, base_url, resume_file=resume_file, status_q=status_q,
                        max_shared_memory=max_shm * 1024 * 1024, max_workers=max_workers,
                        dl_timeout=dl_timeout)
        anlres = dlm.run_analysis(manifest=new_manifest, old_manifest=old_manifest,
                                  patch=not disable_patching, resume=not force,
                                  file_prefix_filter=file_prefix_filter,
                                  file_exclude_filter=file_exclude_filter,
                                  file_install_tag=file_install_tag,
                                  processing_optimization=process_opt)

        prereq = None
        if new_manifest.meta.prereq_ids:
            prereq = dict(ids=new_manifest.meta.prereq_ids, name=new_manifest.meta.prereq_name,
                          path=new_manifest.meta.prereq_path, args=new_manifest.meta.prereq_args)

        offline = game.metadata.get('customAttributes', {}).get('CanRunOffline', {}).get('value', 'true')
        ot = game.metadata.get('customAttributes', {}).get('OwnershipToken', {}).get('value', 'false')

        if file_install_tag is None:
            file_install_tag = []
        igame = InstalledGame(app_name=game.app_name, title=game.app_title,
                              version=new_manifest.meta.build_version, prereq_info=prereq,
                              manifest_path=override_manifest, base_urls=base_urls,
                              install_path=install_path, executable=new_manifest.meta.launch_exe,
                              launch_parameters=new_manifest.meta.launch_command,
                              can_run_offline=offline == 'true', requires_ot=ot == 'true',
                              is_dlc=base_game is not None, install_size=anlres.install_size,
                              egl_guid=egl_guid, install_tags=file_install_tag,
                              platform=platform)

        # game is either up to date or hasn't changed, so we have nothing to do
        if not anlres.dl_size:
            self.log.info('Download size is 0, the game is either already up to date or has not changed. Exiting...')
            self.clean_post_install(game, igame, repair, repair_file)

            raise RuntimeError('Nothing to do.')

        res = self.check_installation_conditions(analysis=anlres, install=igame, game=game,
                                                 updating=self.is_installed(app_name),
                                                 ignore_space_req=ignore_space_req)

        return dlm, anlres, game, igame, repair, repair_file, res

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

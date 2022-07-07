from multiprocessing import Queue

import legendary.core
from legendary.models.downloading import AnalysisResult
from legendary.models.game import Game
from legendary.models.manifest import ManifestMeta

from .exception import LgndrException, LgndrLogHandler
from .manager import DLManager


class LegendaryCore(legendary.core.LegendaryCore):

    def __init__(self, override_config=None, timeout=10.0):
        super(LegendaryCore, self).__init__(override_config=override_config, timeout=timeout)
        self.handler = LgndrLogHandler()
        self.log.addHandler(self.handler)

    def prepare_download(self, game: Game, base_game: Game = None, base_path: str = '',
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
                         disable_https: bool = False) -> (DLManager, AnalysisResult, ManifestMeta):
        _dlmanager = legendary.core.DLManager
        legendary.core.DLManager = DLManager
        try:
            dlm, analysis, igame = super(LegendaryCore, self).prepare_download(
                game=game, base_game=base_game, base_path=base_path,
                status_q=status_q, max_shm=max_shm, max_workers=max_workers,
                force=force, disable_patching=disable_patching,
                game_folder=game_folder, override_manifest=override_manifest,
                override_old_manifest=override_old_manifest, override_base_url=override_base_url,
                platform=platform, file_prefix_filter=file_prefix_filter,
                file_exclude_filter=file_exclude_filter, file_install_tag=file_install_tag,
                dl_optimizations=dl_optimizations, dl_timeout=dl_timeout,
                repair=repair, repair_use_latest=repair_use_latest,
                disable_delta=disable_delta, override_delta_manifest=override_delta_manifest,
                egl_guid=egl_guid, preferred_cdn=preferred_cdn,
                disable_https=disable_https
            )
            # lk: monkeypatch run_real (the method that emits the stats) into DLManager
            # dlm.run_real = DLManager.run_real.__get__(dlm, DLManager)
            return dlm, analysis, igame
        except LgndrException as ret:
            raise ret
        finally:
            legendary.core.DLManager = _dlmanager

    def egl_import(self, app_name):
        try:
            super(LegendaryCore, self).egl_import(app_name)
        except LgndrException as ret:
            raise ret
        finally:
            pass

    def egl_export(self, app_name):
        try:
            super(LegendaryCore, self).egl_export(app_name)
        except LgndrException as ret:
            raise ret
        finally:
            pass

    def prepare_overlay_install(self, path=None, status_q: Queue = None):
        _dlmanager = legendary.core.DLManager
        legendary.core.DLManager = DLManager
        try:
            dlm, analysis_result, igame = super(LegendaryCore, self).prepare_overlay_install(path)
            # lk: monkeypatch status_q (the queue for download stats)
            # lk: and run_real (the method that emits the stats) into DLManager
            dlm.status_queue = status_q
            # dlm.run_real = DLManager.run_real.__get__(dlm, DLManager)
            return dlm, analysis_result, igame
        except LgndrException as ret:
            raise ret
        finally:
            legendary.core.DLManager = _dlmanager

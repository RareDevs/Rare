import os
from custom_legendary.models.downloading import ConditionCheckResult

class InstallOptionsModel:
    def __init__(self, app_name: str, base_path: str = os.path.expanduser("~/legendary"),
                 max_workers: int = os.cpu_count() * 2, repair: bool = False, no_install: bool = False,
                 ignore_space_req: bool = False, force: bool = False, sdl_list: list = ['']
                 ):
        self.app_name = app_name
        self.base_path = base_path
        self.max_workers = max_workers
        self.repair = repair
        self.no_install = no_install
        self.ignore_space_req = ignore_space_req
        self.force = force
        self.sdl_list = sdl_list


class InstallDownloadModel:
    def __init__(self, dlmanager, analysis, game, igame, repair: bool, repair_file: str, res: ConditionCheckResult):
        self.dlmanager = dlmanager
        self.analysis = analysis
        self.game = game
        self.igame = igame
        self.repair = repair
        self.repair_file = repair_file
        self.res = res


class InstallQueueItemModel:
    def __init__(self, status_q=None, download: InstallDownloadModel = None, options: InstallOptionsModel = None):
        self.status_q = status_q
        self.download = download
        self.options = options

    def __bool__(self):
        return (self.status_q is not None) and (self.download is not None) and (self.options is not None)

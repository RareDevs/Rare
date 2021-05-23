import os


class InstallOptionsModel:
    def __init__(self, app_name: str, path: str = os.path.expanduser("~/legendary"),
                 max_workers: int = os.cpu_count() * 2, repair: bool = False, dl_only: bool = False,
                 ignore_space_req: bool = False, force: bool = False, sdl_list: list = ['']
                 ):
        self.app_name = app_name
        self.path = path
        self.max_workers = max_workers
        self.repair = repair
        self.dl_only = dl_only
        self.ignore_space_req = ignore_space_req
        self.force = force
        self.sdl_list = sdl_list


class InstallDownloadModel:
    def __init__(self, dlmanager, analysis, game, igame, repair: bool, repair_file: str):
        self.dlmanager = dlmanager
        self.analysis = analysis
        self.game = game
        self.igame = igame
        self.repair = repair
        self.repair_file = repair_file


class InstallQueueItemModel:
    def __init__(self, status_q=None, download: InstallDownloadModel = None, options: InstallOptionsModel = None):
        self.status_q = status_q
        self.download = download
        self.options = options

    def __bool__(self):
        return (self.status_q is not None) and (self.download is not None) and (self.options is not None)

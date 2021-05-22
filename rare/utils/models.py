import os


class InstallOptionsModel:
    def __init__(self, app_name: str, path: str = os.path.expanduser("~/legendary"),
                 max_workers: int = os.cpu_count() * 2, repair: bool = False, dl_only: bool = False,
                 ignore_free_space: bool = False, force: bool = False, sdl_list: list = ['']
                 ):
        self.app_name = app_name
        self.path = path
        self.max_workers = max_workers
        self.repair = repair
        self.dl_only = dl_only
        self.ignore_free_space = ignore_free_space
        self.force = force
        self.sdl_list = sdl_list


class InstallDownloadModel:
    def __init__(self, dlmanager, analysis, game, igame, repair: bool = False, repair_file: str = None):
        self.dlmanager = dlmanager
        self.analysis = analysis
        self.game = game
        self.igame = igame
        self.repair = repair
        self.repair_file = repair_file


class InstallQueueItemModel:
    def __init__(self, queue, download: InstallDownloadModel, options: InstallOptionsModel):
        self.queue = queue
        self.download = download
        self.options = options

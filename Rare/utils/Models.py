import os


class InstallOptions:
    def __init__(self, app_name: str, path: str = os.path.expanduser("~/legendary"),
                 max_workers: int = os.cpu_count() * 2, repair: bool = False,
                 download_only: bool = False):
        self.app_name = app_name
        self.path = path
        self.max_workers = max_workers
        self.repair = repair
        self.download_only = download_only


class KillDownloadException(Exception):
    pass

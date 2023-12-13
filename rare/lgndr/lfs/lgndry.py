import os

from filelock import FileLock
from legendary.lfs.lgndry import LGDLFS as LGDLFSReal


class LGDLFS(LGDLFSReal):
    def __init__(self, *args, **kwargs):
        super(LGDLFS, self).__init__(*args, **kwargs)
        self.log.info("Using Rare's LGDLFS monkey")
        # Rare: Default FileLock in Python 3.11 is thread-local, so replace it with a non-local verison
        self._installed_lock = FileLock(os.path.join(self.path, 'installed.json') + '.lock', thread_local=False)

    def unlock_installed(self):
        self._installed_lock.release(force=True)

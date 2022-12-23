import os
import subprocess

from PyQt5.QtCore import pyqtSignal, QRunnable, QObject, pyqtSlot

from rare.models.pathspec import PathSpec


class WineResolver(QRunnable):
    class Signals(QObject):
        result_ready = pyqtSignal(str)

    def __init__(self, rare_core, path: str, app_name: str):
        super(WineResolver, self).__init__()
        self.signals = WineResolver.Signals()
        self.setAutoDelete(True)
        self.wine_env = os.environ.copy()
        core = rare_core.core()
        self.wine_env.update(core.get_app_environment(app_name))
        self.wine_env["WINEDLLOVERRIDES"] = "winemenubuilder=d;mscoree=d;mshtml=d;"
        self.wine_env["DISPLAY"] = ""

        self.wine_binary = core.lgd.config.get(
            app_name,
            "wine_executable",
            fallback=core.lgd.config.get("default", "wine_executable", fallback="wine"),
        )
        self.winepath_binary = os.path.join(os.path.dirname(self.wine_binary), "winepath")
        self.path = PathSpec(core, app_name).cook(path)

    @pyqtSlot()
    def run(self):
        if "WINEPREFIX" not in self.wine_env or not os.path.exists(self.wine_env["WINEPREFIX"]):
            # pylint: disable=E1136
            self.signals.result_ready[str].emit("")
            return
        if not os.path.exists(self.wine_binary) or not os.path.exists(self.winepath_binary):
            # pylint: disable=E1136
            self.signals.result_ready[str].emit("")
            return
        path = self.path.strip().replace("/", "\\")
        # lk: if path does not exist form
        cmd = [self.wine_binary, "cmd", "/c", "echo", path]
        # lk: if path exists and needs a case-sensitive interpretation form
        # cmd = [self.wine_binary, 'cmd', '/c', f'cd {path} & cd']
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.wine_env,
            shell=False,
            text=True,
        )
        out, err = proc.communicate()
        # Clean wine output
        out = out.strip().strip('"')
        proc = subprocess.Popen(
            [self.winepath_binary, "-u", out],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.wine_env,
            shell=False,
            text=True,
        )
        out, err = proc.communicate()
        real_path = os.path.realpath(out.strip())
        # pylint: disable=E1136
        self.signals.result_ready[str].emit(real_path)
        return

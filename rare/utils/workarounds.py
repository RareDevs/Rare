import platform
from logging import getLogger

import requests
from orjson import orjson
from PySide6.QtWidgets import QApplication

from rare.utils import config_helper as config
from rare.utils.paths import data_dir
from rare.utils.wrapper_exe import wrapper_path


class Workarounds:
    _workarounds_url = 'https://raredevs.github.io/wring/workarounds.json'
    _workarounds_version_url = 'https://raredevs.github.io/wring/workarounds_version.json'

    def __init__(self):
        self.logger = getLogger(type(self).__name__)
        self._workarounds: dict[str, dict[str, dict[str, dict[str, str | tuple]]]] = {}
        self._active_download: bool = False

    def _download_workarounds(self) -> bytes:
        if self._active_download:
            return b''
        self._active_download = True
        resp = requests.get(self._workarounds_url)
        self._active_download = False
        return resp.content

    def load_workarounds(self) -> dict[str, dict[str, dict[str, dict[str, str | tuple]]]]:
        if self._workarounds:
            return self._workarounds

        try:
            resp = requests.get(self._workarounds_version_url, timeout=1)
            data = resp.content.decode('utf-8')
            remote_version = orjson.loads(data).get('version', 1)
        except requests.exceptions.Timeout:
            remote_version = 1

        file = data_dir().joinpath('workarounds.json')

        if file.is_file():
            json = orjson.loads(file.open('r').read())
            version = json.get('version', 1)
            if version >= remote_version:
                self._workarounds = json.get('workarounds', {})
        else:
            version = 0

        if not file.is_file() or version < remote_version:
            if content := self._download_workarounds():
                data = content.decode('utf-8')
                with file.open('w', encoding='utf-8') as fd:
                    fd.write(data)
                json = orjson.loads(data)
                self._workarounds = json.get('workarounds', {})

        return self._workarounds

    def get(self, app_name: str) -> dict:
        if not self._workarounds:
            self.load_workarounds()
        return self._workarounds.get(app_name, {})

    @staticmethod
    def screen_height() -> int:
        return QApplication.instance().primaryScreen().geometry().height()

    @staticmethod
    def screen_width() -> int:
        return QApplication.instance().primaryScreen().geometry().width()

    @staticmethod
    def wrapper_exe() -> str:
        return str(wrapper_path())

    @staticmethod
    def subst(text: str) -> str:
        return text.format(
            res_width=Workarounds.screen_width(),
            res_height=Workarounds.screen_height(),
            wrapper_exe=Workarounds.wrapper_exe(),
        )


workarounds = Workarounds()


def apply_workarounds(app_name: str):
    if wa := workarounds.get(app_name):
        # apply options
        for opt in (options := wa.get('options', {})):
            if config.get_option(app_name, opt, None) is not None:
                continue
            if platform.system() not in options[opt].get('os', tuple()):
                continue
            config.set_option(app_name, opt, Workarounds.subst(options[opt]['value']))
        # apply environment
        for var in (environ := wa.get('environ', {})):
            if config.get_envvar(app_name, var, None) is not None:
                continue
            if platform.system() not in environ[var].get('os', tuple()):
                continue
            config.set_envvar(app_name, var, Workarounds.subst(environ[var]['value']))


__all__ = ['apply_workarounds', 'workarounds']

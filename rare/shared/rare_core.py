import configparser
import os
from argparse import Namespace
from logging import getLogger
from typing import Optional

from PyQt5.QtCore import QObject

from rare.lgndr.core import LegendaryCore
from rare.models.apiresults import ApiResults
from rare.models.signals import GlobalSignals
from .image_manager import ImageManager

logger = getLogger("RareCore")


class RareCore(QObject):
    _instance: Optional['RareCore'] = None

    def __init__(self, args: Namespace):
        if self._instance is not None:
            raise RuntimeError("RareCore already initialized")
        super(RareCore, self).__init__()
        self._args: Optional[Namespace] = None
        self._signals: Optional[GlobalSignals] = None
        self._core: Optional[LegendaryCore] = None
        self._image_manager: Optional[ImageManager] = None
        self._api_results: Optional[ApiResults] = None

        self.args(args)
        self.signals(init=True)
        self.core(init=True)
        self.image_manager(init=True)

        RareCore._instance = self

    @staticmethod
    def instance() -> 'RareCore':
        if RareCore._instance is None:
            raise RuntimeError("Uninitialized use of RareCore")
        return RareCore._instance

    def signals(self, init: bool = False) -> GlobalSignals:
        if self._signals is None and not init:
            raise RuntimeError("Uninitialized use of GlobalSignalsSingleton")
        if self._signals is not None and init:
            raise RuntimeError("GlobalSignals already initialized")
        if init:
            self._signals = GlobalSignals()
        return self._signals

    def args(self, args: Namespace = None) -> Optional[Namespace]:
        if self._args is None and args is None:
            raise RuntimeError("Uninitialized use of ArgumentsSingleton")
        if self._args is not None and args is not None:
            raise RuntimeError("Arguments already initialized")
        if args is not None:
            self._args = args
        return self._args

    def core(self, init: bool = False) -> LegendaryCore:
        if self._core is None and not init:
            raise RuntimeError("Uninitialized use of LegendaryCoreSingleton")
        if self._core is not None and init:
            raise RuntimeError("LegendaryCore already initialized")
        if init:
            try:
                self._core = LegendaryCore()
            except configparser.MissingSectionHeaderError as e:
                logger.warning(f"Config is corrupt: {e}")
                if config_path := os.environ.get("XDG_CONFIG_HOME"):
                    path = os.path.join(config_path, "legendary")
                else:
                    path = os.path.expanduser("~/.config/legendary")
                with open(os.path.join(path, "config.ini"), "w") as config_file:
                    config_file.write("[Legendary]")
                self._core = LegendaryCore()
            if "Legendary" not in self._core.lgd.config.sections():
                self._core.lgd.config.add_section("Legendary")
                self._core.lgd.save_config()
            # workaround if egl sync enabled, but no programdata_path
            # programdata_path might be unset if logging in through the browser
            if self._core.egl_sync_enabled:
                if self._core.egl.programdata_path is None:
                    self._core.lgd.config.remove_option("Legendary", "egl_sync")
                    self._core.lgd.save_config()
                else:
                    if not os.path.exists(self._core.egl.programdata_path):
                        self._core.lgd.config.remove_option("Legendary", "egl_sync")
                        self._core.lgd.save_config()
        return self._core

    def image_manager(self, init: bool = False) -> ImageManager:
        if self._image_manager is None and not init:
            raise RuntimeError("Uninitialized use of ImageManagerSingleton")
        if self._image_manager is not None and init:
            raise RuntimeError("ImageManager already initialized")
        if self._image_manager is None:
            self._image_manager = ImageManager(self.signals(), self.core())
        return self._image_manager

    def api_results(self, res: ApiResults = None) -> Optional[ApiResults]:
        if self._api_results is None and res is None:
            raise RuntimeError("Uninitialized use of ApiResultsSingleton")
        if self._api_results is not None and res is not None:
            raise RuntimeError("ApiResults already initialized")
        if res is not None:
            self._api_results = res
        return self._api_results

    def deleteLater(self) -> None:
        del self._api_results
        self._api_results = None

        self._image_manager.deleteLater()
        del self._image_manager
        self._image_manager = None

        self._core.exit()
        del self._core
        self._core = None

        self._signals.deleteLater()
        del self._signals
        self._signals = None

        del self._args
        self._args = None

        RareCore._instance = None

        super(RareCore, self).deleteLater()


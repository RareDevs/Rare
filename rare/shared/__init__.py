"""
Shared controller resources module

Each of the objects in this module should be instantiated ONCE
and only ONCE!
"""

import configparser
import logging
import os
from argparse import Namespace
from typing import Optional, Union

from rare.lgndr.core import LegendaryCore
from rare.models.apiresults import ApiResults
from rare.models.signals import GlobalSignals

logger = logging.getLogger("Singleton")

_legendary_core_singleton: Optional[LegendaryCore] = None
_global_signals_singleton: Optional[GlobalSignals] = None
_arguments_singleton: Optional[Namespace] = None
_api_results_singleton: Optional[ApiResults] = None


def LegendaryCoreSingleton(init: bool = False) -> LegendaryCore:
    global _legendary_core_singleton
    if _legendary_core_singleton is None and not init:
        raise RuntimeError("Uninitialized use of LegendaryCoreSingleton")
    if _legendary_core_singleton is not None and init:
        raise RuntimeError("LegendaryCore already initialized")
    if init:
        try:
            _legendary_core_singleton = LegendaryCore()
        except configparser.MissingSectionHeaderError as e:
            logger.warning(f"Config is corrupt: {e}")
            if config_path := os.environ.get("XDG_CONFIG_HOME"):
                path = os.path.join(config_path, "legendary")
            else:
                path = os.path.expanduser("~/.config/legendary")
            with open(os.path.join(path, "config.ini"), "w") as config_file:
                config_file.write("[Legendary]")
            _legendary_core_singleton = LegendaryCore()
        if "Legendary" not in _legendary_core_singleton.lgd.config.sections():
            _legendary_core_singleton.lgd.config.add_section("Legendary")
            _legendary_core_singleton.lgd.save_config()
        # workaround if egl sync enabled, but no programdata_path
        # programdata_path might be unset if logging in through the browser
        if _legendary_core_singleton.egl_sync_enabled:
            if _legendary_core_singleton.egl.programdata_path is None:
                _legendary_core_singleton.lgd.config.remove_option("Legendary", "egl_sync")
                _legendary_core_singleton.lgd.save_config()
            else:
                if not os.path.exists(_legendary_core_singleton.egl.programdata_path):
                    _legendary_core_singleton.lgd.config.remove_option("Legendary", "egl_sync")
                    _legendary_core_singleton.lgd.save_config()
    return _legendary_core_singleton


def GlobalSignalsSingleton(init: bool = False) -> GlobalSignals:
    global _global_signals_singleton
    if _global_signals_singleton is None and not init:
        raise RuntimeError("Uninitialized use of GlobalSignalsSingleton")
    if _global_signals_singleton is not None and init:
        raise RuntimeError("GlobalSignals already initialized")
    if init:
        _global_signals_singleton = GlobalSignals()
    return _global_signals_singleton


def ArgumentsSingleton(args: Namespace = None) -> Optional[Namespace]:
    global _arguments_singleton
    if _arguments_singleton is None and args is None:
        raise RuntimeError("Uninitialized use of ArgumentsSingleton")
    if _arguments_singleton is not None and args is not None:
        raise RuntimeError("Arguments already initialized")
    if args is not None:
        _arguments_singleton = args
    return _arguments_singleton


def ApiResultsSingleton(res: ApiResults = None) -> Optional[ApiResults]:
    global _api_results_singleton
    if _api_results_singleton is None and res is None:
        raise RuntimeError("Uninitialized use of ApiResultsSingleton")
    if _api_results_singleton is not None and res is not None:
        raise RuntimeError("ApiResults already initialized")
    if res is not None:
        _api_results_singleton = res
    return _api_results_singleton


def clear_singleton_instance(instance: Union[LegendaryCore, GlobalSignals, Namespace, ApiResults]):
    global _legendary_core_singleton, _global_signals_singleton, _arguments_singleton, _api_results_singleton
    if isinstance(instance, LegendaryCore):
        del instance
        _legendary_core_singleton = None
    elif isinstance(instance, GlobalSignals):
        instance.deleteLater()
        del instance
        _global_signals_singleton = None
    elif isinstance(instance, Namespace):
        del instance
        _arguments_singleton = None
    elif isinstance(instance, ApiResults):
        del instance
        _api_results_singleton = None
    else:
        raise RuntimeError(f"Instance is of unknown type \"{type(instance)}\"")

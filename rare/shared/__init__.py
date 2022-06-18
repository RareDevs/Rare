"""
Shared controller resources module

Each of the objects in this module should be instantiated ONCE
and only ONCE!
"""

from argparse import Namespace
from typing import Optional

from legendary.core import LegendaryCore

from rare.models.apiresults import ApiResults
from rare.models.signals import GlobalSignals

_legendary_core_singleton: Optional[LegendaryCore] = None
_global_signals_singleton: Optional[GlobalSignals] = None
_arguments_singleton: Optional[Namespace] = None
_api_results_singleton: Optional[ApiResults] = None


def LegendaryCoreSingleton(init: bool = False) -> LegendaryCore:
    global _legendary_core_singleton
    if _legendary_core_singleton is None and not init:
        raise RuntimeError("Uninitialized use of LegendaryCoreSingleton")
    if _legendary_core_singleton is None:
        _legendary_core_singleton = LegendaryCore()
    return _legendary_core_singleton


def GlobalSignalsSingleton(init: bool = False) -> GlobalSignals:
    global _global_signals_singleton
    if _global_signals_singleton is None and not init:
        raise RuntimeError("Uninitialized use of GlobalSignalsSingleton")
    if _global_signals_singleton is None:
        _global_signals_singleton = GlobalSignals()
    return _global_signals_singleton


def ArgumentsSingleton(args: Namespace = None) -> Optional[Namespace]:
    global _arguments_singleton
    if _arguments_singleton is None and args is None:
        raise RuntimeError("Uninitialized use of ArgumentsSingleton")
    if _arguments_singleton is None:
        _arguments_singleton = args
    return _arguments_singleton


def ApiResultsSingleton(res: ApiResults = None) -> Optional[ApiResults]:
    global _api_results_singleton
    if _api_results_singleton is None and res is None:
        raise RuntimeError("Uninitialized use of ApiResultsSingleton")
    if _api_results_singleton is None:
        _api_results_singleton = res
    return _api_results_singleton


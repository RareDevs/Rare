"""
Shared controller resources module

Each of the objects in this module should be instantiated ONCE
and only ONCE!
"""

from argparse import Namespace
from typing import Optional

from rare.lgndr.cli import LegendaryCLI
from rare.lgndr.core import LegendaryCore

from rare.models.apiresults import ApiResults
from rare.models.signals import GlobalSignals

_legendary_cli_signleton: Optional[LegendaryCLI] = None
_legendary_core_singleton: Optional[LegendaryCore] = None
_global_signals_singleton: Optional[GlobalSignals] = None
_arguments_singleton: Optional[Namespace] = None
_api_results_singleton: Optional[ApiResults] = None


def LegendaryCLISingleton(init: bool = False) -> LegendaryCLI:
    global _legendary_cli_signleton
    if _legendary_cli_signleton is None and not init:
        raise RuntimeError("Uninitialized use of LegendaryCLISingleton")
    if _legendary_cli_signleton is None:
        _legendary_cli_signleton = LegendaryCLI(override_config=None, api_timeout=10)
    return _legendary_cli_signleton


def LegendaryCoreSingleton(init: bool = False) -> LegendaryCore:
    global _legendary_cli_signleton
    if _legendary_cli_signleton is None:
        raise RuntimeError("LegendaryCLI is not initialized yet")
    # if _legendary_cli_signleton is None:
    #     _legendary_cli_signleton = LegendaryCLISingleton(init)
    return _legendary_cli_signleton.core


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


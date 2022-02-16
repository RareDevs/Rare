from argparse import Namespace

from legendary.core import LegendaryCore
from rare.utils.models import ApiResults, GlobalSignals

_legendary_core_singleton: LegendaryCore = None
_global_signals_singleton: GlobalSignals = None
_arguments_singleton: Namespace = None
_api_results_singleton: ApiResults = None


def LegendaryCoreSingleton() -> LegendaryCore:
    global _legendary_core_singleton
    if _legendary_core_singleton is None:
        _legendary_core_singleton = LegendaryCore()
    return _legendary_core_singleton


def GlobalSignalsSingleton() -> GlobalSignals:
    global _global_signals_singleton
    if _global_signals_singleton is None:
        _global_signals_singleton = GlobalSignals()
    return _global_signals_singleton


def ArgumentsSingleton(args: Namespace = None) -> Namespace:
    global _arguments_singleton
    if _arguments_singleton is None:
        _arguments_singleton = args
    return _arguments_singleton


def ApiResultsSingleton(res: ApiResults = None) -> ApiResults:
    global _api_results_singleton
    if _api_results_singleton is None:
        _api_results_singleton = res
    return _api_results_singleton


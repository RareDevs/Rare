from argparse import Namespace

from legendary.core import LegendaryCore
from rare.utils.models import Signals, ApiResults

legendary_core: LegendaryCore = None
signals: Signals = None
args: Namespace = None
api_results: ApiResults = None


def init_legendary():
    global legendary_core
    legendary_core = LegendaryCore()
    return legendary_core


def init_signals():
    global signals
    signals = Signals()
    return signals


def init_args(a: Namespace):
    global args
    args = a


def init_api_response(res: ApiResults):
    global api_results
    api_results = res

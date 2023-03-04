"""
Shared controller resources module

Each of the objects in this module should be instantiated ONCE
and only ONCE!
"""

import logging
from argparse import Namespace
from typing import Optional

from rare.lgndr.core import LegendaryCore
from rare.models.signals import GlobalSignals
from .image_manager import ImageManager
from .rare_core import RareCore

logger = logging.getLogger("Shared")


def ArgumentsSingleton() -> Optional[Namespace]:
    return RareCore.instance().args()


def GlobalSignalsSingleton() -> GlobalSignals:
    return RareCore.instance().signals()


def LegendaryCoreSingleton() -> LegendaryCore:
    return RareCore.instance().core()


def ImageManagerSingleton() -> ImageManager:
    return RareCore.instance().image_manager()

"""
Shared controller resources module

Each of the objects in this module should be instantiated ONCE
and only ONCE!
"""

import logging

from .image_manager import ImageManager
from .rare_core import RareCore

logger = logging.getLogger("Shared")

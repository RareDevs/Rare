from enum import Enum
from typing import Tuple

from PyQt5.QtCore import QSize


class Orientation(Enum):
    Tall = 0
    Wide = 1
    Icon = 3
    Logo = 2


class ImageSize:
    class Preset:
        def __init__(self, divisor: float, pixel_ratio: float, orientation: Orientation = Orientation.Tall,
                     base: 'ImageSize.Preset' = None):
            self.__divisor = divisor
            self.__pixel_ratio = pixel_ratio
            if orientation == Orientation.Tall:
                self.__img_factor = 67
                self.__size = QSize(self.__img_factor * 3, self.__img_factor * 4) * pixel_ratio / divisor
            if orientation == Orientation.Wide:
                self.__img_factor = 34
                self.__size = QSize(self.__img_factor * 16, self.__img_factor * 9) * pixel_ratio / divisor
            if orientation == Orientation.Icon:
                self.__img_factor = 128
                self.__size = QSize(self.__img_factor * 1, self.__img_factor * 1) * pixel_ratio / divisor
            self.__orientation = orientation
            # lk: for prettier images set this to true
            # self.__smooth_transform: bool = True
            self.__smooth_transform = divisor <= 2
            self.__base = base if base is not None else self

        def __eq__(self, other: 'ImageSize.Preset'):
            return (
                self.__size == other.size
                and self.__divisor == other.divisor
                and self.__smooth_transform == other.smooth
                and self.__pixel_ratio == other.pixel_ratio
            )

        @property
        def size(self) -> QSize:
            return self.__size

        @property
        def divisor(self) -> float:
            return self.__divisor

        @property
        def smooth(self) -> bool:
            return self.__smooth_transform

        @property
        def pixel_ratio(self) -> float:
            return self.__pixel_ratio

        @property
        def orientation(self) -> Orientation:
            return self.__orientation

        @property
        def aspect_ratio(self) -> Tuple[int, int]:
            if self.__orientation == Orientation.Tall:
                return 3, 4
            elif self.__orientation == Orientation.Wide:
                return 16, 9
            else:
                return 0, 0

        @property
        def base(self) -> 'ImageSize.Preset':
            return self.__base

    Image = Preset(1, 1)
    """! @brief Size and pixel ratio of the image on disk"""

    ImageWide = Preset(1, 1, Orientation.Wide)
    """! @brief Size and pixel ratio for wide 16/9 image on disk"""

    Display = Preset(1, 1, base=Image)
    """! @brief Size and pixel ratio for displaying"""

    DisplayWide = Preset(2, 1, Orientation.Wide, base=ImageWide)
    """! @brief Size and pixel ratio for wide 16/9 image display"""

    LibraryWide = Preset(2.41, 1, Orientation.Wide, base=ImageWide)

    Library = Preset(1.21, 1, base=Image)
    """! @brief Same as Display"""

    Small = Preset(3, 1, base=Image)
    """! @brief Small image size for displaying"""

    SmallWide = Preset(6, 1, Orientation.Wide, base=ImageWide)
    """! @brief Small image size for displaying"""

    Smaller = Preset(4, 1, base=Image)
    """! @brief Smaller image size for displaying"""

    SmallerWide = Preset(8, 1, Orientation.Wide, base=ImageWide)
    """! @brief Smaller image size for displaying"""

    Smallest = Preset(5, 1, base=Image)
    """! @brief Smaller image size for UI icons"""

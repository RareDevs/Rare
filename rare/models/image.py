from enum import Enum

from PyQt5.QtCore import QSize


class Orientation(Enum):
    Tall = 0
    Wide = 1


class ImageSize:
    class Preset:
        def __init__(self, divisor: float, pixel_ratio: float, orientation: Orientation = Orientation.Tall,
                     base: 'ImageSize.Preset' = None):
            self.__divisor = divisor
            self.__pixel_ratio = pixel_ratio
            if orientation == Orientation.Tall:
                self.__img_factor = 67
                self.__size = QSize(self.__img_factor * 3, self.__img_factor * 4) * pixel_ratio / divisor
            else:
                self.__img_factor = 17
                self.__size = QSize(self.__img_factor * 16, self.__img_factor * 9) * pixel_ratio / divisor
            # lk: for prettier images set this to true
            self.__smooth_transform: bool = True
            if divisor > 2:
                self.__smooth_transform = False

            if base is not None:
                self.__base = base
            else:
                self.__base = self

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
        def base(self) -> 'ImageSize.Preset':
            return self.__base

    Image = Preset(1, 2)
    """! @brief Size and pixel ratio of the image on disk"""

    ImageWide = Preset(1, 2, Orientation.Wide)
    """! @brief Size and pixel ratio for wide 16/9 image on disk"""

    Display = Preset(1, 1, base=Image)
    """! @brief Size and pixel ratio for displaying"""

    DisplayWide = Preset(1, 1, Orientation.Wide, base=ImageWide)
    """! @brief Size and pixel ratio for wide 16/9 image display"""

    Wide = DisplayWide

    Normal = Display
    """! @brief Same as Display"""

    Small = Preset(3, 1, base=Image)
    """! @brief Small image size for displaying"""

    SmallWide = Preset(1, 1, Orientation.Wide, base=ImageWide)
    """! @brief Small image size for displaying"""

    Smaller = Preset(4, 1, base=Image)
    """! @brief Smaller image size for displaying"""

    SmallerWide = Preset(4, 1, Orientation.Wide, base=ImageWide)
    """! @brief Smaller image size for displaying"""

    Icon = Preset(5, 1, base=Image)
    """! @brief Smaller image size for UI icons"""

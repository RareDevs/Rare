from enum import IntEnum


class LibraryView(IntEnum):
    COVER = 1
    VLIST = 2


class LibraryFilter(IntEnum):
    ALL = 1
    INSTALLED = 2
    OFFLINE = 3
    HIDDEN = 4
    WIN32 = 5
    MAC = 6
    INSTALLABLE = 7
    INCLUDE_UE = 8


class LibraryOrder(IntEnum):
    TITLE = 1
    RECENT = 2
    NEWEST = 3
    OLDEST = 4

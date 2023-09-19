import os
import shlex
from hashlib import md5
from enum import IntEnum
from typing import Dict, List, Union


class WrapperType(IntEnum):
    NONE = 0
    COMPAT_TOOL = 1
    LEGENDARY_IMPORT = 8
    USER_DEFINED = 9


class Wrapper:
    def __init__(self, command: Union[str, List[str]], name: str = None, wtype: WrapperType = None):
        self.__command: List[str] = shlex.split(command) if isinstance(command, str) else command
        self.__name: str = name if name is not None else os.path.basename(self.__command[0])
        self.__wtype: WrapperType = wtype if wtype is not None else WrapperType.USER_DEFINED

    @property
    def is_compat_tool(self) -> bool:
        return self.__wtype == WrapperType.COMPAT_TOOL

    @property
    def is_editable(self) -> bool:
        return self.__wtype == WrapperType.USER_DEFINED or self.__wtype == WrapperType.LEGENDARY_IMPORT

    @property
    def checksum(self) -> str:
        return md5(self.command.encode("utf-8")).hexdigest()

    @property
    def executable(self) -> str:
        return shlex.quote(self.__command[0])

    @property
    def command(self) -> str:
        return " ".join(shlex.quote(part) for part in self.__command)

    @property
    def name(self) -> str:
        return self.__name

    @property
    def type(self) -> WrapperType:
        return self.__wtype

    def __eq__(self, other) -> bool:
        return self.command == other.command

    def __hash__(self):
        return hash(self.__command)

    def __bool__(self) -> bool:
        if not self.is_editable:
            return True
        return bool(self.command.strip())

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            command=data.get("command"),
            name=data.get("name"),
            wtype=WrapperType(data.get("wtype", WrapperType.USER_DEFINED))
        )

    @property
    def __dict__(self):
        return dict(
            command=self.__command,
            name=self.__name,
            wtype=int(self.__wtype)
        )

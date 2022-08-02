import logging
from dataclasses import dataclass

from typing_extensions import Protocol


class GetBooleanChoiceProtocol(Protocol):
    def __call__(self, prompt: str, default: bool = ...) -> bool:
        ...


def get_boolean_choice(prompt: str, default: bool = True) -> bool:
    return default


def verify_stdout(a0: int, a1: int, a2: float, a3: float) -> None:
    print(f"Verification progress: {a0}/{a1} ({a2:.01f}%) [{a3:.1f} MiB/s]\t\r")


class DLManagerSignals:
    _kill = False
    _update = False

    @property
    def kill(self) -> bool:
        self._update = False
        return self._kill

    @kill.setter
    def kill(self, value: bool) -> None:
        self._update = True
        self._kill = value

    @property
    def update(self) -> bool:
        _update = self._update
        self._update = False
        return _update


@dataclass
class LgndrIndirectStatus:
    success: bool = False
    message: str = ""

    def __len__(self):
        if self.message:
            return 2
        else:
            return 0

    def __bool__(self):
        return self.success

    def __getitem__(self, item):
        if item == 0:
            return self.success
        elif item == 1:
            return self.message
        else:
            raise IndexError

    def __iter__(self):
        return iter((self.success, self.message))

    def __str__(self):
        return self.message


class LgndrIndirectLogger:
    def __init__(
        self, status: LgndrIndirectStatus, logger: logging.Logger = None, level: int = logging.ERROR
    ):
        self.logger = logger
        self.level = level
        self.status = status

    def set_logger(self, logger: logging.Logger):
        self.logger = logger

    def set_level(self, level: int):
        self.level = level

    def _log(self, level: int, msg: str):
        self.status.success = True if level < self.level else False
        self.status.message = msg
        if self.logger:
            self.logger.log(level, msg)

    def debug(self, msg: str):
        self._log(logging.DEBUG, msg)

    def info(self, msg: str):
        self._log(logging.INFO, msg)

    def warning(self, msg: str):
        self._log(logging.WARNING, msg)

    def error(self, msg: str):
        self._log(logging.ERROR, msg)

    def critical(self, msg: str):
        self._log(logging.CRITICAL, msg)

    def fatal(self, msg: str):
        self.critical(msg)

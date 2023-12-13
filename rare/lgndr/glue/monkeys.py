import logging
from dataclasses import dataclass
from typing import Protocol, List, Optional, Dict

from rare.lgndr.models.downloading import UIUpdate

logger = logging.getLogger("LgndrMonkeys")


class GetBooleanChoiceProtocol(Protocol):
    def __call__(self, prompt: str, default: bool = ...) -> bool:
        ...


def get_boolean_choice_factory(value: bool = True) -> GetBooleanChoiceProtocol:
    def get_boolean_choice(prompt: str, default: bool = value) -> bool:
        logger.debug("get_boolean_choice: %s, default: %s, choice: %s", prompt, default, value)
        return value
    return get_boolean_choice


class SdlPromptProtocol(Protocol):
    def __call__(self, sdl_data: Dict, title: str) -> List[str]:
        ...


def sdl_prompt_factory(install_tag: Optional[List[str]] = None) -> SdlPromptProtocol:
    def sdl_prompt(sdl_data: Dict, title: str) -> List[str]:
        logger.debug("sdl_prompt: %s", title)
        for key in sdl_data.keys():
            logger.debug("%s: %s %s", key, sdl_data[key]["tags"], sdl_data[key]["name"])
        tags = install_tag if install_tag is not None else [""]
        logger.debug("choice: %s, tags: %s", install_tag, tags)
        return tags
    return sdl_prompt


class VerifyStdoutProtocol(Protocol):
    def __call__(self, a0: int, a1: int, a2: float, a3: float) -> None:
        ...


def verify_stdout_factory(callback: VerifyStdoutProtocol = None) -> VerifyStdoutProtocol:
    def verify_stdout(a0: int, a1: int, a2: float, a3: float) -> None:
        if callback is not None and callable(callback):
            callback(a0, a1, a2, a3)
        else:
            logger.info("Verification progress: %d/%d (%.01f%%) [%.1f MiB/s]", a0, a1, a2, a3)
    return verify_stdout


class UiUpdateProtocol(Protocol):
    def __call__(self, status: UIUpdate) -> None:
        ...


def ui_update_factory(callback: UiUpdateProtocol = None) -> UiUpdateProtocol:
    def ui_update(status: UIUpdate) -> None:
        if callback is not None and callable(callback):
            callback(status)
        else:
            logger.info("Installation progress: %s", status)
    return ui_update


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

import logging
from dataclasses import dataclass

from PyQt5.QtWidgets import QMessageBox, QLabel


def get_boolean_choice(prompt, default=True):
    choice = QMessageBox.question(
        None, "Import DLCs?", prompt,
        defaultButton=QMessageBox.Yes if default else QMessageBox.No
    )
    return True if choice == QMessageBox.StandardButton.Yes else False


def return_exit(__status):
    return __status


class UILogHandler(logging.Handler):
    def __init__(self, dest: QLabel):
        super(UILogHandler, self).__init__()
        self.widget = dest

    def emit(self, record: logging.LogRecord) -> None:
        self.widget.setText(record.getMessage())


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
    def __init__(self, status: LgndrIndirectStatus, logger: logging.Logger = None, level: int = logging.ERROR):
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

import logging

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


class LgndrReturnLogger:
    def __init__(self, logger: logging.Logger, level: int = logging.ERROR):
        self.logger = logger
        self.level = level
        self.value = False
        self.message = ""

    def _log(self, level: int, msg: str):
        self.value = True if level < self.level else False
        self.message = msg
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

    def __len__(self):
        if self.message:
            return 2
        else:
            return 0

    def __bool__(self):
        return self.value

    def __getitem__(self, item):
        if item == 0:
            return self.value
        elif item == 1:
            return self.message
        else:
            raise IndexError

    def __iter__(self):
        return iter((self.value, self.message))

    def __str__(self):
        return self.message

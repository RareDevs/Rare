import logging

from PyQt5.QtWidgets import QMessageBox, QLabel


def get_boolean_choice(a0):
    choice = QMessageBox.question(None, "Import DLCs?", a0)
    return True if choice == QMessageBox.StandardButton.Yes else False


def return_exit(__status):
    return __status


class UILogHandler(logging.Handler):
    def __init__(self, dest: QLabel):
        super(UILogHandler, self).__init__()
        self.widget = dest

    def emit(self, record: logging.LogRecord) -> None:
        self.widget.setText(record.getMessage())
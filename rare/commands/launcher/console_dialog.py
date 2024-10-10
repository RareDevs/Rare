import os
from typing import Union

from PySide6.QtCore import QProcessEnvironment, Signal, QSize, Qt
from PySide6.QtGui import QTextCursor, QFont, QCursor, QCloseEvent
from PySide6.QtWidgets import (
    QPlainTextEdit,
    QDialog,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QSpacerItem,
    QSizePolicy, QTableWidgetItem, QHeaderView, QApplication,
)

from rare.ui.commands.launcher.console_env import Ui_ConsoleEnv
from rare.widgets.dialogs import dialog_title, game_title


class ConsoleDialog(QDialog):
    term = Signal()
    kill = Signal()
    env: QProcessEnvironment

    def __init__(self, app_title: str, parent=None):
        super(ConsoleDialog, self).__init__(parent=parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setWindowTitle(
            dialog_title(game_title(self.tr("Console"), app_title))
        )
        self.setGeometry(0, 0, 640, 480)
        layout = QVBoxLayout()

        self.console_edit = ConsoleEdit(self)
        layout.addWidget(self.console_edit)

        button_layout = QHBoxLayout()

        self.env_button = QPushButton(self.tr("Show environment"))
        button_layout.addWidget(self.env_button)
        self.env_button.clicked.connect(self.show_env)

        self.save_button = QPushButton(self.tr("Save output to file"))
        button_layout.addWidget(self.save_button)
        self.save_button.clicked.connect(self.save)

        self.clear_button = QPushButton(self.tr("Clear console"))
        button_layout.addWidget(self.clear_button)
        self.clear_button.clicked.connect(self.console_edit.clear)

        button_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))

        self.terminate_button = QPushButton(self.tr("Terminate"))
        # self.terminate_button.setVisible(platform.system() == "Windows")
        button_layout.addWidget(self.terminate_button)
        self.terminate_button.clicked.connect(lambda: self.term.emit())

        self.kill_button = QPushButton(self.tr("Kill"))
        # self.kill_button.setVisible(platform.system() == "Windows")
        button_layout.addWidget(self.kill_button)
        self.kill_button.clicked.connect(lambda: self.kill.emit())

        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.env_variables = ConsoleEnv(app_title, self)
        self.env_variables.hide()

        self.accept_close = False

    def show(self) -> None:
        super(ConsoleDialog, self).show()
        self.center_window()

    def center_window(self):
        # get the margins of the decorated window
        margins = self.windowHandle().frameMargins()
        # get the screen the cursor is on
        current_screen = QApplication.screenAt(QCursor.pos())
        if not current_screen:
            current_screen = QApplication.primaryScreen()
        # get the available screen geometry (excludes panels/docks)
        screen_rect = current_screen.availableGeometry()
        decor_width = margins.left() + margins.right()
        decor_height = margins.top() + margins.bottom()
        window_size = QSize(self.width(), self.height()).boundedTo(
            screen_rect.size() - QSize(decor_width, decor_height)
        )

        self.resize(window_size)
        self.move(
            screen_rect.center()
            - self.rect().adjusted(0, 0, decor_width, decor_height).center()
        )

    def save(self):
        file, ok = QFileDialog.getSaveFileName(
            self, "Save output", "", "Log Files (*.log);;All Files (*)"
        )
        if ok:
            if "." not in file:
                file += ".log"
            with open(file, "w", encoding="utf-8") as f:
                f.write(self.console_edit.toPlainText())
                f.close()
                self.save_button.setText(self.tr("Saved"))

    def set_env(self, env: QProcessEnvironment):
        self.env = env

    def show_env(self):
        self.env_variables.setTable(self.env)
        self.env_variables.show()

    def log(self, text: str):
        self.console_edit.log(f"Rare: {text}")

    def log_stdout(self, text: str):
        self.console_edit.log(text)

    def error(self, text):
        self.console_edit.error(f"Rare: {text}")

    def log_stderr(self, text):
        self.console_edit.error(text)

    def on_process_exit(self, app_title: str, status: Union[int, str]):
        self.error(
            self.tr("Application finished with exit code \"{}\"").format(status)
        )
        self.accept_close = True

    def reject(self) -> None:
        self.close()

    def accept(self) -> None:
        self.close()

    def closeEvent(self, a0: QCloseEvent) -> None:
        if self.accept_close:
            super(ConsoleDialog, self).closeEvent(a0)
            a0.accept()
        else:
            self.showMinimized()
            a0.ignore()


class ConsoleEnv(QDialog):

    def __init__(self, app_title: str, parent=None):
        super(ConsoleEnv, self).__init__(parent=parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.ui = Ui_ConsoleEnv()
        self.ui.setupUi(self)
        self.setWindowTitle(
            dialog_title(game_title(self.tr("Environment"), app_title))
        )

    def setTable(self, env: QProcessEnvironment):
        self.ui.table.clearContents()
        self.ui.table.setRowCount(len(env.keys()))

        for idx, key in enumerate(env.keys()):
            self.ui.table.setItem(idx, 0, QTableWidgetItem(env.keys()[idx]))
            self.ui.table.setItem(idx, 1, QTableWidgetItem(env.value(env.keys()[idx])))

        self.ui.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)


class ConsoleEdit(QPlainTextEdit):

    def __init__(self, parent=None):
        super(ConsoleEdit, self).__init__(parent=parent)
        self.setReadOnly(True)
        font = QFont("Monospace")
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

    def scroll_to_last_line(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.movePosition(
            QTextCursor.MoveOperation.Up if cursor.atBlockStart() else QTextCursor.MoveOperation.StartOfLine
        )
        self.setTextCursor(cursor)

    def print_to_console(self, text: str, color: str):
        html = f"<p style=\"color:{color};white-space:pre\">{text}</p>"
        self.appendHtml(html)
        self.scroll_to_last_line()

    def log(self, text):
        self.print_to_console(text, "#aaa")

    def error(self, text):
        self.print_to_console(text, "#a33")

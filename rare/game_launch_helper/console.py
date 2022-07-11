import platform

from PyQt5.QtCore import QProcessEnvironment, pyqtSignal
from PyQt5.QtGui import QTextCursor, QFont
from PyQt5.QtWidgets import (
    QPlainTextEdit,
    QDialog,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QSpacerItem,
    QSizePolicy, QTableWidgetItem, QHeaderView,
)

from rare.ui.components.extra.console_env import Ui_ConsoleEnv


class Console(QDialog):
    term = pyqtSignal()
    kill = pyqtSignal()
    env: QProcessEnvironment

    def __init__(self, parent=None):
        super(Console, self).__init__(parent=parent)
        self.setWindowTitle("Rare - Console")
        self.setGeometry(0, 0, 600, 400)
        layout = QVBoxLayout()

        self.console = ConsoleEdit(self)
        layout.addWidget(self.console)

        button_layout = QHBoxLayout()

        self.env_button = QPushButton(self.tr("Show environment"))
        button_layout.addWidget(self.env_button)
        self.env_button.clicked.connect(self.show_env)

        self.save_button = QPushButton(self.tr("Save output to file"))
        button_layout.addWidget(self.save_button)
        self.save_button.clicked.connect(self.save)

        self.clear_button = QPushButton(self.tr("Clear console"))
        button_layout.addWidget(self.clear_button)
        self.clear_button.clicked.connect(self.console.clear)

        button_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))

        self.terminate_button = QPushButton(self.tr("Terminate"))
        self.terminate_button.setVisible(platform.system() == "Windows")
        button_layout.addWidget(self.terminate_button)
        self.terminate_button.clicked.connect(lambda: self.term.emit())

        self.kill_button = QPushButton(self.tr("Kill"))
        self.kill_button.setVisible(platform.system() == "Windows")
        button_layout.addWidget(self.kill_button)
        self.kill_button.clicked.connect(lambda: self.kill.emit())

        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.env_variables = ConsoleEnv(self)
        self.env_variables.hide()

    def save(self):
        file, ok = QFileDialog.getSaveFileName(
            self, "Save output", "", "Log Files (*.log);;All Files (*)"
        )
        if ok:
            if "." not in file:
                file += ".log"
            with open(file, "w") as f:
                f.write(self.console.toPlainText())
                f.close()
                self.save_button.setText(self.tr("Saved"))

    def set_env(self, env: QProcessEnvironment):
        self.env = env

    def show_env(self):
        self.env_variables.setTable(self.env)
        self.env_variables.show()

    def log(self, text: str, end: str = "\n"):
        self.console.log(text + end)

    def error(self, text, end: str = "\n"):
        self.console.error(text + end)


class ConsoleEnv(QDialog):

    def __init__(self, parent=None):
        super(ConsoleEnv, self).__init__(parent=parent)
        self.ui = Ui_ConsoleEnv()
        self.ui.setupUi(self)

    def setTable(self, env: QProcessEnvironment):
        self.ui.table.clearContents()
        self.ui.table.setRowCount(len(env.keys()))

        for idx, key in enumerate(env.keys()):
            self.ui.table.setItem(idx, 0, QTableWidgetItem(env.keys()[idx]))
            self.ui.table.setItem(idx, 1, QTableWidgetItem(env.value(env.keys()[idx])))

        self.ui.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)


class ConsoleEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super(ConsoleEdit, self).__init__(parent=parent)
        self.setReadOnly(True)
        self.setFont(QFont("monospace"))
        self._cursor_output = self.textCursor()

    def log(self, text):
        html = f"<p style=\"color:#999;white-space:pre\">{text}</p>"
        self._cursor_output.insertHtml(html)
        self.scroll_to_last_line()

    def error(self, text):
        html = f"<p style=\"color:#eee;white-space:pre\">{text}</p>"
        self._cursor_output.insertHtml(html)
        self.scroll_to_last_line()

    def scroll_to_last_line(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.movePosition(
            QTextCursor.Up if cursor.atBlockStart() else QTextCursor.StartOfLine
        )
        self.setTextCursor(cursor)

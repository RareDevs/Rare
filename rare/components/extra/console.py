from PyQt5.QtCore import Qt, QCoreApplication, QMetaObject, QProcessEnvironment
from PyQt5.QtGui import QTextCursor, QFont
from PyQt5.QtWidgets import (
    QPlainTextEdit,
    QDialog,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QSpacerItem,
    QSizePolicy, QTableWidget, QTableWidgetItem, QAbstractItemView, QDialogButtonBox, QHeaderView,
)


class ConsoleWindow(QDialog):
    env: QProcessEnvironment

    def __init__(self, parent=None):
        super(ConsoleWindow, self).__init__(parent=parent)
        self.setWindowTitle("Rare Console")
        self.setGeometry(0, 0, 600, 400)
        layout = QVBoxLayout()

        self.console = Console(self)
        layout.addWidget(self.console)

        button_layout = QHBoxLayout()
        button_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))

        self.env_button = QPushButton(self.tr("Show environment"))
        button_layout.addWidget(self.env_button)
        self.env_button.clicked.connect(self.show_env)

        self.save_button = QPushButton(self.tr("Save output to file"))
        button_layout.addWidget(self.save_button)
        self.save_button.clicked.connect(self.save)

        self.clear_button = QPushButton(self.tr("Clear console"))
        button_layout.addWidget(self.clear_button)
        self.clear_button.clicked.connect(self.console.clear)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.env_variables = EnvVariables(self)
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


class EnvVariables(QDialog):

    class Ui(object):
        def __init__(self, container):
            layout = QVBoxLayout()
            self.table = QTableWidget(container)
            self.table.setColumnCount(2)

            self.table.setHorizontalHeaderItem(0, QTableWidgetItem())
            self.table.setHorizontalHeaderItem(1, QTableWidgetItem())
            font = QFont()
            font.setFamily(u"Monospace")
            self.table.setFont(font)
            self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.table.setAlternatingRowColors(True)
            self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.table.setSortingEnabled(True)
            self.table.setCornerButtonEnabled(True)
            self.table.horizontalHeader().setVisible(True)
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.verticalHeader().setVisible(False)
            self.table.horizontalHeaderItem(0).setText(container.tr("Variable"))
            self.table.horizontalHeaderItem(1).setText(container.tr("Value"))
            layout.addWidget(self.table)

            self.buttons = QDialogButtonBox(container)
            self.buttons.setOrientation(Qt.Horizontal)
            self.buttons.setStandardButtons(QDialogButtonBox.Close)
            self.buttons.accepted.connect(container.accept)
            self.buttons.rejected.connect(container.reject)
            layout.addWidget(self.buttons)

            container.setLayout(layout)
            container.setObjectName(type(self).__name__)
            container.setWindowTitle("Rare Console Environment")
            container.setGeometry(0, 0, 600, 400)

    def __init__(self, parent=None):
        super(EnvVariables, self).__init__(parent=parent)
        self.ui = EnvVariables.Ui(self)

    def setTable(self, env: QProcessEnvironment):
        self.ui.table.clearContents()
        self.ui.table.setRowCount(len(env.keys()))

        for idx, key in enumerate(env.keys()):
            self.ui.table.setItem(idx, 0, QTableWidgetItem(env.keys()[idx]))
            self.ui.table.setItem(idx, 1, QTableWidgetItem(env.value(env.keys()[idx])))

        self.ui.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)


class Console(QPlainTextEdit):
    def __init__(self, parent=None):
        super(Console, self).__init__(parent=parent)
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

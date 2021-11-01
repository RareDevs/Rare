from PyQt5.QtGui import QTextCursor, QFont
from PyQt5.QtWidgets import QPlainTextEdit, QWidget, QPushButton, QFileDialog, QVBoxLayout


class ConsoleWindow(QWidget):
    def __init__(self):
        super(ConsoleWindow, self).__init__()
        self.layout = QVBoxLayout()
        self.setGeometry(0, 0, 600, 400)

        self.console = Console()
        self.layout.addWidget(self.console)

        self.save_button = QPushButton(self.tr("Save output to file"))
        self.layout.addWidget(self.save_button)
        self.save_button.clicked.connect(self.save)

        self.clear_button = QPushButton(self.tr("Clear"))
        self.layout.addWidget(self.clear_button)
        self.clear_button.clicked.connect(self.console.clear)

        self.setLayout(self.layout)

    def save(self):
        file, ok = QFileDialog.getSaveFileName(self, "Save output", "", "Log Files (*.log);;All Files (*)")
        if ok:
            if "." not in file:
                file += ".log"
            with open(file, "w") as f:
                f.write(self.console.toPlainText())
                f.close()
                self.save_button.setText(self.tr("Saved"))

    def log(self, text):
        self.console.log(text)

    def error(self, text):
        self.console.error(text)


class Console(QPlainTextEdit):

    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFont("monospace"))
        self._cursor_output = self.textCursor()

    def log(self, text):
        self._cursor_output.insertText(text)
        self.scroll_to_last_line()

    def error(self, text):
        self._cursor_output.insertHtml(f"<font color=\"Red\">{text}</font>")
        self.scroll_to_last_line()

    def scroll_to_last_line(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.movePosition(QTextCursor.Up if cursor.atBlockStart() else
                            QTextCursor.StartOfLine)
        self.setTextCursor(cursor)

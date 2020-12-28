import os

from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QLabel


class InstallDialog(QDialog):
    def __init__(self, game):
        super(InstallDialog, self).__init__()
        self.setWindowTitle("Install Game")
        self.layout = QVBoxLayout()
        self.yes = False
        self.install_path = QLineEdit(f"{os.path.expanduser('~')}/legendary")
        self.options = QLabel("Verschiedene Optionene")
        self.layout.addWidget(self.options)

        self.layout.addStretch(1)
        self.yes_button = QPushButton("Install")
        self.yes_button.clicked.connect(self.close)
        self.cancel_button = QPushButton("cancel")

        self.layout.addWidget(self.options)
        self.layout.addWidget(self.install_path)

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.yes_button)
        self.button_layout.addWidget(self.cancel_button)
        self.yes_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.cancel)
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)

    def get_data(self) -> dict:
        self.exec_()
        return {
            "install_path": self.install_path.text()
        } if self.yes else 0

    def accept(self):
        self.yes = True
        self.close()

    def cancel(self):
        self.yes = False
        self.close()


class AcceptDialog(QDialog):
    def __init__(self, text: str):
        super(AcceptDialog, self).__init__()
        self.accept_status = False
        self.text = QLabel(text)
        self.accept_button = QPushButton("Yes")
        self.accept_button.clicked.connect(self.accept)
        self.exit_button = QPushButton("Cancel")
        self.exit_button.clicked.connect(self.cancel)
        self.layout = QVBoxLayout()
        self.child_layout = QHBoxLayout()

        self.layout.addWidget(self.text)
        self.child_layout.addStretch(1)
        self.child_layout.addWidget(self.accept_button)
        self.child_layout.addWidget(self.exit_button)

        self.layout.addStretch(1)
        self.layout.addLayout(self.child_layout)
        self.setLayout(self.layout)

    def get_accept(self):
        self.exec_()
        return self.accept_status

    def accept(self):
        self.accept_status = True
        self.close()

    def cancel(self):
        self.accept_status = False
        self.close()

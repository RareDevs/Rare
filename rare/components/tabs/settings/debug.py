import os

from PyQt5.QtCore import QProcess
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton

from rare.shared import GlobalSignalsSingleton, ArgumentsSingleton
from rare.utils import utils
from rare.utils.paths import data_dir


class DebugSettings(QWidget):
    def __init__(self):
        super(DebugSettings, self).__init__()
        self.setLayout(QVBoxLayout())

        self.raise_runtime_exception_button = QPushButton("Raise Exception")
        self.layout().addWidget(self.raise_runtime_exception_button)
        self.raise_runtime_exception_button.clicked.connect(self.raise_exception)

        self.restart_button = QPushButton("Restart")
        self.layout().addWidget(self.restart_button)
        self.restart_button.clicked.connect(self.restart)
        self.layout().addStretch(1)

    def restart(self):
        executable = utils.get_rare_executable()
        if os.path.exists(os.path.join(data_dir, "singleton.lock")):
            os.remove(os.path.join(data_dir, "singleton.lock"))
        GlobalSignalsSingleton().exit_app.emit(0)
        if ArgumentsSingleton().debug:
            executable.append("--debug")
        QProcess.startDetached(executable[0], executable[1:])

    def raise_exception(self):
        raise RuntimeError("Debug Crash")

from PyQt5.QtCore import Qt, pyqtSignal, QCoreApplication
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import (
    QDialog,
    QLabel,
    QVBoxLayout,
    QCheckBox,
    QHBoxLayout,
    QPushButton,
)
from legendary.utils.selective_dl import get_sdl_appname

from rare.models.game import RareGame
from rare.models.install import UninstallOptionsModel
from rare.utils.misc import icon


class UninstallDialog(QDialog):
    result_ready = pyqtSignal(UninstallOptionsModel)

    def __init__(self, rgame: RareGame, options: UninstallOptionsModel, parent=None):
        super(UninstallDialog, self).__init__(parent=parent)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        header = self.tr("Uninstall")
        self.setWindowTitle(f'{header} "{rgame.app_title}" - {QCoreApplication.instance().applicationName()}')
        self.info_text = QLabel(
            self.tr("Do you really want to uninstall <b>{}</b>?").format(rgame.app_title)
        )

        self.keep_files = QCheckBox(self.tr("Keep game files."))
        self.keep_files.setChecked(bool(options.keep_files))
        self.keep_config = QCheckBox(self.tr("Keep game configuation."))
        self.keep_config.setChecked(bool(options.keep_config))

        self.uninstall_button = QPushButton(
            icon("ei.remove-circle", color="red"), self.tr("Uninstall")
        )
        self.uninstall_button.setObjectName("UninstallButton")
        self.uninstall_button.clicked.connect(self.__on_uninstall)

        self.cancel_button = QPushButton(self.tr("Cancel"))
        self.cancel_button.clicked.connect(self.__on_cancel)

        form_layout = QVBoxLayout()
        form_layout.setContentsMargins(-1, -1, 0, -1)
        form_layout.addWidget(self.keep_files)
        form_layout.addWidget(self.keep_config)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.uninstall_button)

        layout = QVBoxLayout()
        layout.addWidget(self.info_text)
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        if get_sdl_appname(rgame.app_name) is not None:
            self.keep_config.setChecked(True)

        self.options: UninstallOptionsModel = options

    def closeEvent(self, a0: QCloseEvent) -> None:
        self.result_ready.emit(self.options)
        super(UninstallDialog, self).closeEvent(a0)

    def __on_uninstall(self):
        self.options.values = (True, self.keep_files.isChecked(), self.keep_config.isChecked())
        self.close()

    def __on_cancel(self):
        self.options.values = (None, None, None)
        self.close()

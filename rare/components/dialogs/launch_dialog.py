import platform
from logging import getLogger

from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QDialog, QApplication
from requests.exceptions import ConnectionError, HTTPError

from rare.components.dialogs.login import LoginDialog
from rare.shared import RareCore
from rare.ui.components.dialogs.launch_dialog import Ui_LaunchDialog
from rare.widgets.elide_label import ElideLabel

logger = getLogger("LaunchDialog")


class LaunchDialog(QDialog):
    quit_app = pyqtSignal(int)
    start_app = pyqtSignal()

    def __init__(self, parent=None):
        super(LaunchDialog, self).__init__(parent=parent)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(
            Qt.Window
            | Qt.Dialog
            | Qt.CustomizeWindowHint
            | Qt.WindowSystemMenuHint
            | Qt.WindowTitleHint
            | Qt.WindowMinimizeButtonHint
            | Qt.MSWindowsFixedSizeDialogHint
        )
        self.setWindowModality(Qt.WindowModal)
        self.ui = Ui_LaunchDialog()
        self.ui.setupUi(self)

        self.accept_close = False

        self.progress_info = ElideLabel(parent=self)
        self.progress_info.setFixedHeight(False)
        self.ui.launch_layout.addWidget(self.progress_info)

        self.rcore = RareCore.instance()
        self.rcore.progress.connect(self.__on_progress)
        self.rcore.completed.connect(self.__on_completed)
        self.core = self.rcore.core()
        self.args = self.rcore.args()

        self.login_dialog = LoginDialog(core=self.core, parent=parent)

    def login(self):
        do_launch = True
        try:
            if self.args.offline:
                pass
            else:
                # Force an update check and notice in case there are API changes
                self.core.check_for_updates(force=True)
                self.core.force_show_update = True
                if self.core.login():
                    logger.info("You are logged in")
                else:
                    raise ValueError("You are not logged in. Open Login Window")
        except ValueError as e:
            logger.info(str(e))
            # Do not set parent, because it won't show a task bar icon
            # Update: Inherit the same parent as LaunchDialog
            do_launch = self.login_dialog.login()
        except (HTTPError, ConnectionError) as e:
            logger.warning(e)
            self.args.offline = True
        finally:
            if do_launch:
                if not self.args.silent:
                    self.show()
                self.launch()
            else:
                self.quit_app.emit(0)

    def launch(self):
        self.progress_info.setText(self.tr("Preparing Rare"))
        self.rcore.fetch()

    @pyqtSlot(int, str)
    def __on_progress(self, i: int, m: str):
        self.ui.progress_bar.setValue(i)
        self.progress_info.setText(m)

    def __on_completed(self):
        logger.info("App starting")
        self.accept_close = True
        self.start_app.emit()

    def reject(self) -> None:
        if self.accept_close:
            super(LaunchDialog, self).reject()
        else:
            pass

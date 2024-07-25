from logging import getLogger

from PySide6.QtCore import Qt, Signal, Slot
from requests.exceptions import ConnectionError, HTTPError

from rare.components.dialogs.login import LoginDialog
from rare.shared import RareCore
from rare.ui.components.dialogs.launch_dialog import Ui_LaunchDialog
from rare.widgets.dialogs import BaseDialog
from rare.widgets.elide_label import ElideLabel

logger = getLogger("LaunchDialog")


class LaunchDialog(BaseDialog):
    # lk: the reason we use the `start_app` signal here instead of accepted, is to keep the dialog
    # until the main window has been created, then we call `accept()` to close the dialog
    start_app = Signal()

    def __init__(self, parent=None):
        super(LaunchDialog, self).__init__(parent=parent)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.MSWindowsFixedSizeDialogHint
        )

        self.ui = Ui_LaunchDialog()
        self.ui.setupUi(self)

        self.progress_info = ElideLabel(parent=self)
        self.progress_info.setFixedHeight(False)
        self.ui.launch_layout.addWidget(self.progress_info)

        self.rcore = RareCore.instance()
        self.rcore.progress.connect(self.__on_progress)
        self.rcore.completed.connect(self.__on_completed)
        self.core = self.rcore.core()
        self.args = self.rcore.args()

        self.login_dialog = LoginDialog(core=self.core, parent=parent)
        self.login_dialog.rejected.connect(self.reject)
        self.login_dialog.accepted.connect(self.do_launch)

    def login(self):
        can_launch = True
        try:
            if not self.args.offline:
                # Force an update check and notice in case there are API changes
                # self.core.check_for_updates(force=True)
                # self.core.force_show_update = True
                if not self.core.login(force_refresh=True):
                    raise ValueError("You are not logged in. Opening login window.")
                logger.info("You are logged in")
                self.login_dialog.close()
        except ValueError as e:
            logger.info(str(e))
            # Do not set parent, because it won't show a task bar icon
            # Update: Inherit the same parent as LaunchDialog
            can_launch = False
            self.login_dialog.open()
        except (HTTPError, ConnectionError) as e:
            logger.warning(e)
            self.args.offline = True
        finally:
            if can_launch:
                self.do_launch()

    @Slot()
    def do_launch(self):
        if not self.args.silent:
            self.open()
        self.launch()

    def launch(self):
        self.progress_info.setText(self.tr("Preparing Rare"))
        self.rcore.fetch()

    @Slot(int, str)
    def __on_progress(self, i: int, m: str):
        self.ui.progress_bar.setValue(i)
        self.progress_info.setText(m)

    def __on_completed(self):
        logger.info("App starting")
        self.start_app.emit()

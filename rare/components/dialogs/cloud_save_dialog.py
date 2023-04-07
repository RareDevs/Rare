import datetime
import sys
from logging import getLogger

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QSizePolicy, QLayout, QApplication, QWidget
from legendary.core import LegendaryCore
from legendary.models.game import InstalledGame

from rare.ui.components.dialogs.sync_save_dialog import Ui_SyncSaveDialog
from rare.ui.components.tabs.games.game_info.sync_widget import Ui_SyncWidget
from rare.utils.misc import icon

logger = getLogger("Cloud Saves")


class CloudSaveDialog(QDialog, Ui_SyncSaveDialog):
    DOWNLOAD = 2
    UPLOAD = 1
    CANCEL = 0
    SKIP = 3

    def __init__(
        self,
        igame: InstalledGame,
        dt_local: datetime.datetime,
        dt_remote: datetime.datetime,
    ):
        super(CloudSaveDialog, self).__init__()
        self.setupUi(self)

        self.sync_widget = QWidget()
        self.sync_ui = Ui_SyncWidget()
        self.sync_ui.setupUi(self.sync_widget)

        self.sync_widget_layout.addWidget(self.sync_widget)

        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)

        self.status = self.CANCEL

        self.title_label.setText(f"{self.title_label.text()} <b>{igame.title}</b>")

        newer = self.tr("Newer")
        if dt_remote and dt_local:
            self.sync_ui.age_label_local.setText(
                f"<b>{newer}</b>" if dt_remote < dt_local else " "
            )
            self.sync_ui.age_label_remote.setText(
                f"<b>{newer}</b>" if dt_remote > dt_local else " "
            )
        # Set status, if one of them is None
        elif dt_remote and not dt_local:
            self.status = self.DOWNLOAD
        elif not dt_remote and dt_local:
            self.status = self.UPLOAD
        else:
            self.status = self.SKIP

        self.sync_ui.date_info_local.setText(dt_local.strftime("%A, %d. %B %Y %X") if dt_local else "None")
        self.sync_ui.date_info_remote.setText(dt_remote.strftime("%A, %d. %B %Y %X") if dt_remote else "None")

        self.sync_ui.icon_local.setPixmap(icon("mdi.harddisk", "fa.desktop").pixmap(128, 128))
        self.sync_ui.icon_remote.setPixmap(icon("mdi.cloud-outline", "ei.cloud").pixmap(128, 128))

        self.sync_ui.upload_button.clicked.connect(lambda: self.btn_clicked(self.UPLOAD))
        self.sync_ui.download_button.clicked.connect(lambda: self.btn_clicked(self.DOWNLOAD))
        self.cancel_button.clicked.connect(self.close)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.layout().setSizeConstraint(QLayout.SetFixedSize)

    def get_action(self):
        if self.status == self.SKIP:
            return self.SKIP
        self.exec_()
        return self.status

    def btn_clicked(self, status):
        self.status = status
        self.close()


def test_dialog():
    app = QApplication(sys.argv)
    core = LegendaryCore()
    dlg = CloudSaveDialog(core.get_installed_list()[0], datetime.datetime.now(),
                          datetime.datetime.strptime("2021,1", "%Y,%M"))
    print(dlg.get_action())


if __name__ == '__main__':
    test_dialog()

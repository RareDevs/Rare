import os
import platform
from logging import getLogger
from typing import List

from PyQt5.QtCore import QRunnable, QObject, pyqtSignal, QThreadPool
from PyQt5.QtWidgets import QGroupBox, QFormLayout, QMessageBox

from legendary.utils import eos
from rare import shared
from rare.components.dialogs.install_dialog import InstallDialog
from rare.ui.components.tabs.settings.eos_widget import Ui_EosWidget
from rare.utils.models import InstallOptionsModel

logger = getLogger("EOS")


class InstallOverlayDialog(InstallDialog):
    def __init__(self):
        super(InstallOverlayDialog, self).__init__()

        self.layout = QFormLayout()


def get_wine_prefixes() -> List[str]:
    prefixes = [os.path.expanduser("~/.wine")]
    for i in shared.core.get_installed_list():
        env = shared.core.get_app_environment(i.app_name)
        if pfx := env.get("WINEPREFIX"):
            if pfx not in prefixes:
                prefixes.append(pfx)
        if steam_pfx := env.get("STEAM_COMPAT_DATA_PATH"):
            if steam_pfx not in prefixes:
                prefixes.append(os.path.join(steam_pfx, "pfx"))
    return prefixes


class WorkerSignals(QObject):
    update_available = pyqtSignal(bool)


class CheckForUpdateWorker(QRunnable):
    def __init__(self):
        super(CheckForUpdateWorker, self).__init__()
        self.setAutoDelete(True)
        self.signals = WorkerSignals()

    def run(self) -> None:
        shared.core.check_for_overlay_updates()
        self.signals.update_available.emit(shared.core.overlay_update_available)


class EosWidget(QGroupBox, Ui_EosWidget):
    def __init__(self):
        super(EosWidget, self).__init__()
        self.setupUi(self)
        self.core = shared.core

        self.prefix_enabled = False

        self.info_stack.addWidget(self.installed_info_gb)
        self.info_stack.addWidget(self.install_overlay_gb)

        self.enabled_cb.stateChanged.connect(self.change_enable)
        self.uninstall_button.clicked.connect(self.uninstall_overlay)

        self.update_button.setVisible(False)
        self.update_info_lbl.setVisible(False)
        self.overlay = self.core.lgd.get_overlay_install_info()

        shared.signals.overlay_installation_finished.connect(self.overlay_installation_finished)

        self.update_check_button.clicked.connect(self.check_for_update)
        self.install_button.clicked.connect(self.install_overlay)
        self.update_button.clicked.connect(lambda: self.install_overlay(True))

        if self.overlay:  # installed
            self.installed_version_lbl.setText(self.overlay.version)
            self.installed_path_lbl.setText(self.overlay.install_path)
        else:
            self.info_stack.setCurrentIndex(1)
            self.enable_gb.setDisabled(True)

        if platform.system() == "Windows":
            self.current_prefix = None
            self.select_pfx_combo.setVisible(False)
        else:
            self.current_prefix = os.path.expanduser("~/.wine")
            for pfx in get_wine_prefixes():
                self.select_pfx_combo.addItem(pfx.replace(os.path.expanduser("~/"), "~/"))
            self.select_pfx_combo.currentIndexChanged.connect(self.update_select_combo)
            self.update_select_combo(None)

        reg_paths = eos.query_registry_entries(self.current_prefix)
        enabled = False
        if reg_paths['overlay_path'] and self.core.is_overlay_install(reg_paths['overlay_path']):
            enabled = True

        self.enabled_cb.setChecked(enabled)
        self.enabled_info_label.setText("")

    def check_for_update(self):
        def worker_finished(update_available):
            self.update_button.setVisible(update_available)
            self.update_info_lbl.setVisible(update_available)
            self.update_check_button.setDisabled(False)

        self.update_check_button.setDisabled(True)
        worker = CheckForUpdateWorker()
        worker.signals.update_available.connect(worker_finished)
        QThreadPool.globalInstance().start(worker)

    def overlay_installation_finished(self):
        self.overlay = self.core.lgd.get_overlay_install_info()

        if not self.overlay:
            logger.error("Something went wrong, when installing overlay")
            QMessageBox.warning(self, "Error", self.tr("Something went wrong, when installing overlay"))
            return

        self.info_stack.setCurrentIndex(0)
        self.installed_version_lbl.setText(self.overlay.version)
        self.installed_path_lbl.setText(self.overlay.install_path)

        self.update_button.setVisible(False)
        self.update_info_lbl.setVisible(False)

        self.enable_gb.setEnabled(True)

    def update_select_combo(self, i: None):
        if i is None:
            i = self.select_pfx_combo.currentIndex()
        prefix = self.select_pfx_combo.itemText(i).replace("~/", os.path.expanduser("~/"))
        self.current_prefix = prefix
        reg_paths = eos.query_registry_entries(self.current_prefix)

        overlay_enabled = False
        if reg_paths['overlay_path'] and self.core.is_overlay_install(reg_paths['overlay_path']):
            overlay_enabled = True
        self.enabled_cb.setChecked(overlay_enabled)

    def change_enable(self):
        enabled = self.enabled_cb.isChecked()
        if not enabled:
            eos.remove_registry_entries(self.current_prefix)
            logger.info("Disabled Epic Overlay")
            self.enabled_info_label.setText(self.tr("Disabled"))
        else:
            if not self.overlay:
                available_installs = self.core.search_overlay_installs(self.current_prefix)
                if not available_installs:
                    logger.error('No EOS overlay installs found!')
                    return
                path = available_installs[0]
            else:
                path = self.overlay.install_path

            if not self.core.is_overlay_install(path):
                logger.error(f'Not a valid Overlay installation: {path}')
                self.select_pfx_combo.removeItem(self.select_pfx_combo.currentIndex())
                return

            path = os.path.normpath(path)
            reg_paths = eos.query_registry_entries(self.current_prefix)
            if old_path := reg_paths["overlay_path"]:
                if os.path.normpath(old_path) == path:
                    logger.info(f'Overlay already enabled, nothing to do.')
                    return
                else:
                    logger.info(f'Updating overlay registry entries from "{old_path}" to "{path}"')
                eos.remove_registry_entries(self.current_prefix)
            eos.add_registry_entries(path, self.current_prefix)
            self.enabled_info_label.setText(self.tr("Enabled"))
            logger.info(f'Enabled overlay at: {path}')

    def update_checkbox(self):
        reg_paths = eos.query_registry_entries(self.current_prefix)
        enabled = False
        if reg_paths['overlay_path'] and self.core.is_overlay_install(reg_paths['overlay_path']):
            enabled = True
        self.enabled_cb.setChecked(enabled)

    def install_overlay(self, update=False):

        base_path = os.path.expanduser("~/legendary/.overlay")
        if update:
            if not self.overlay:
                self.info_stack.setCurrentIndex(1)
                self.enable_gb.setDisabled(True)
                QMessageBox.warning(self, "Warning", self.tr("Overlay is not installed. Could not update"))
                return
            base_path = self.overlay.install_path

        options = InstallOptionsModel(app_name="", base_path=base_path,
                                      platform="Windows", overlay=True)

        shared.signals.install_game.emit(options)

    def uninstall_overlay(self):
        if not self.core.is_overlay_installed():
            logger.error('No legendary-managed overlay installation found.')
            self.info_stack.setCurrentIndex(1)
            return

        if QMessageBox.No == QMessageBox.question(
                self, "Uninstall Overlay", self.tr("Do you want to uninstall overlay?"),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ):
            return
        if platform.system() == "Windows":
            eos.remove_registry_entries(None)
        else:
            for prefix in [self.select_pfx_combo.itemText(i) for i in range(self.select_pfx_combo.count())]:
                try:
                    eos.remove_registry_entries(os.path.expanduser(prefix))
                except:
                    pass

        self.core.remove_overlay_install()
        self.info_stack.setCurrentIndex(1)

        self.enable_gb.setDisabled(True)

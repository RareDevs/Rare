import os
import platform
from logging import getLogger
from typing import List

from PyQt5.QtCore import QRunnable, QObject, pyqtSignal, QThreadPool
from PyQt5.QtWidgets import QGroupBox, QMessageBox
from legendary.lfs import eos

from rare.models.install import InstallOptionsModel
from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton
from rare.ui.components.tabs.games.integrations.eos_widget import Ui_EosWidget

logger = getLogger("EOS")


def get_wine_prefixes() -> List[str]:
    prefixes = list()
    if os.path.exists(p := os.path.expanduser("~/.wine")):
        prefixes.append(p)

    for name, section in LegendaryCoreSingleton().lgd.config.items():
        pfx = section.get("WINEPREFIX") or section.get("wine_prefix")
        if pfx and pfx not in prefixes:
            prefixes.append(pfx)

    return prefixes


class CheckForUpdateWorker(QRunnable):
    class CheckForUpdateSignals(QObject):
        update_available = pyqtSignal(bool)

    def __init__(self):
        super(CheckForUpdateWorker, self).__init__()
        self.signals = self.CheckForUpdateSignals()
        self.setAutoDelete(True)
        self.core = LegendaryCoreSingleton()

    def run(self) -> None:
        self.core.check_for_overlay_updates()
        self.signals.update_available.emit(self.core.overlay_update_available)


class EOSGroup(QGroupBox, Ui_EosWidget):
    def __init__(self, parent=None):
        super(EOSGroup, self).__init__(parent=parent)
        self.setupUi(self)
        # lk: set object names for CSS properties
        self.install_button.setObjectName("InstallButton")
        self.uninstall_button.setObjectName("UninstallButton")

        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()

        self.prefix_enabled = False

        self.enabled_cb.stateChanged.connect(self.change_enable)
        self.uninstall_button.clicked.connect(self.uninstall_overlay)

        self.update_button.setVisible(False)
        self.overlay = self.core.lgd.get_overlay_install_info()

        self.signals.application.overlay_installed.connect(self.overlay_installation_finished)
        self.signals.application.prefix_updated.connect(self.update_prefixes)

        self.update_check_button.clicked.connect(self.check_for_update)
        self.install_button.clicked.connect(self.install_overlay)
        self.update_button.clicked.connect(lambda: self.install_overlay(True))

        if self.overlay:  # installed
            self.installed_version_lbl.setText(f"<b>{self.overlay.version}</b>")
            self.installed_path_lbl.setText(f"<b>{self.overlay.install_path}</b>")
            self.overlay_stack.setCurrentIndex(0)
        else:
            self.overlay_stack.setCurrentIndex(1)
            self.enable_frame.setDisabled(True)

        if platform.system() == "Windows":
            self.current_prefix = None
            self.select_pfx_combo.setVisible(False)
        else:
            self.current_prefix = os.path.expanduser("~/.wine") \
                if os.path.exists(os.path.expanduser("~/.wine")) \
                else None
            pfxs = get_wine_prefixes()
            for pfx in pfxs:
                self.select_pfx_combo.addItem(pfx.replace(os.path.expanduser("~/"), "~/"))
            if not pfxs:
                self.enable_frame.setDisabled(True)
            else:
                self.select_pfx_combo.setCurrentIndex(0)

            self.select_pfx_combo.currentIndexChanged.connect(self.update_select_combo)
            if pfxs:
                self.update_select_combo(None)

        self.enabled_info_label.setText("")

        self.threadpool = QThreadPool.globalInstance()

    def update_prefixes(self):
        logger.debug("Updated prefixes")
        pfxs = get_wine_prefixes()  # returns /home/whatever
        self.select_pfx_combo.clear()

        for pfx in pfxs:
            self.select_pfx_combo.addItem(pfx.replace(os.path.expanduser("~/"), "~/"))

        if self.current_prefix in pfxs:
            self.select_pfx_combo.setCurrentIndex(
                self.select_pfx_combo.findText(self.current_prefix.replace(os.path.expanduser("~/"), "~/")))

    def check_for_update(self):
        def worker_finished(update_available):
            self.update_button.setVisible(update_available)
            self.update_check_button.setDisabled(False)
            if not update_available:
                self.update_check_button.setText(self.tr("No update available"))

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

        self.overlay_stack.setCurrentIndex(0)
        self.installed_version_lbl.setText(f"<b>{self.overlay.version}</b>")
        self.installed_path_lbl.setText(f"<b>{self.overlay.install_path}</b>")

        self.update_button.setVisible(False)

        self.enable_frame.setEnabled(True)

    def update_select_combo(self, i: None):
        if i is None:
            i = self.select_pfx_combo.currentIndex()
        prefix = os.path.expanduser(self.select_pfx_combo.itemText(i))
        if platform.system() != "Windows" and not os.path.exists(prefix):
            return
        self.current_prefix = prefix
        reg_paths = eos.query_registry_entries(self.current_prefix)

        overlay_enabled = False
        if reg_paths['overlay_path'] and self.core.is_overlay_install(reg_paths['overlay_path']):
            overlay_enabled = True
        self.enabled_cb.setChecked(overlay_enabled)

    def change_enable(self):
        enabled = self.enabled_cb.isChecked()
        if not enabled:
            try:
                eos.remove_registry_entries(self.current_prefix)
            except PermissionError:
                logger.error("Can't disable eos overlay")
                QMessageBox.warning(self, "Error", self.tr(
                    "Failed to disable Overlay. Probably it is installed by Epic Games Launcher"))
                return
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
                try:
                    eos.remove_registry_entries(self.current_prefix)
                except PermissionError:
                    logger.error("Can't disable eos overlay")
                    QMessageBox.warning(self, "Error", self.tr(
                        "Failed to disable Overlay. Probably it is installed by Epic Games Launcher"))
                    return
            try:
                eos.add_registry_entries(path, self.current_prefix)
            except PermissionError:
                logger.error("Failed to disable eos overlay")
                QMessageBox.warning(self, "Error", self.tr(
                    "Failed to enable EOS overlay. Maybe it is already installed by Epic Games Launcher"))
                return
            self.enabled_info_label.setText(self.tr("Enabled"))
            logger.info(f'Enabled overlay at: {path}')

    def update_checkbox(self):
        reg_paths = eos.query_registry_entries(self.current_prefix)
        enabled = False
        if reg_paths['overlay_path'] and self.core.is_overlay_install(reg_paths['overlay_path']):
            enabled = True
        self.enabled_cb.setChecked(enabled)

    def install_overlay(self, update=False):
        base_path = os.path.join(
            self.core.lgd.config.get("Legendary", "install_dir", fallback=os.path.expanduser("~/legendary")),".overlay"
        )
        if update:
            if not self.overlay:
                self.overlay_stack.setCurrentIndex(1)
                self.enable_frame.setDisabled(True)
                QMessageBox.warning(self, "Warning", self.tr("Overlay is not installed. Could not update"))
                return
            base_path = self.overlay.install_path

        options = InstallOptionsModel(
            app_name=eos.EOSOverlayApp.app_name, base_path=base_path, platform="Windows", overlay=True
        )

        self.signals.game.install.emit(options)

    def uninstall_overlay(self):
        if not self.core.is_overlay_installed():
            logger.error('No legendary-managed overlay installation found.')
            self.overlay_stack.setCurrentIndex(1)
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
                logger.info(f"Removing registry entries from {prefix}")
                try:
                    eos.remove_registry_entries(os.path.expanduser(prefix))
                except Exception as e:
                    logger.warning(f"{prefix}: {e}")

        self.core.remove_overlay_install()
        self.overlay_stack.setCurrentIndex(1)

        self.enable_frame.setDisabled(True)

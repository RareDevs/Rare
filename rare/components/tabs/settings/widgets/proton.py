import os
from logging import getLogger
from pathlib import Path
from typing import Tuple

from PyQt5.QtWidgets import QGroupBox, QFileDialog

from rare.components.tabs.settings import LinuxSettings
from .wrapper import WrapperSettings
from rare.ui.components.tabs.settings.proton import Ui_ProtonSettings
from rare.utils import config_helper
from rare.utils.extra_widgets import PathEdit
from rare.shared import LegendaryCoreSingleton

logger = getLogger("Proton")


def find_proton_combos():
    possible_proton_combos = []
    compatibilitytools_dirs = [
        os.path.expanduser("~/.steam/steam/steamapps/common"),
        "/usr/share/steam/compatibilitytools.d",
        os.path.expanduser("~/.steam/compatibilitytools.d"),
        os.path.expanduser("~/.steam/root/compatibilitytools.d"),
    ]
    for c in compatibilitytools_dirs:
        if os.path.exists(c):
            for i in os.listdir(c):
                proton = os.path.join(c, i, "proton")
                compatibilitytool = os.path.join(c, i, "compatibilitytool.vdf")
                toolmanifest = os.path.join(c, i, "toolmanifest.vdf")
                if os.path.exists(proton) and (
                        os.path.exists(compatibilitytool) or os.path.exists(toolmanifest)
                ):
                    wrapper = f'"{proton}" run'
                    possible_proton_combos.append(wrapper)
    if not possible_proton_combos:
        logger.warning("Unable to find any Proton version")
    return possible_proton_combos


class ProtonSettings(QGroupBox, Ui_ProtonSettings):

    app_name: str
    changeable = True

    def __init__(self, linux_settings: LinuxSettings, wrapper_settings: WrapperSettings):
        super(ProtonSettings, self).__init__()
        self.setupUi(self)
        self._linux_settings = linux_settings
        self._wrapper_settings = wrapper_settings
        self.core = LegendaryCoreSingleton()
        self.possible_proton_combos = find_proton_combos()

        self.proton_combo.addItems(self.possible_proton_combos)
        self.proton_combo.currentIndexChanged.connect(self.change_proton)

        self.proton_prefix = PathEdit(
            file_type=QFileDialog.DirectoryOnly,
            edit_func=self.proton_prefix_edit,
            save_func=self.proton_prefix_save,
            placeholder=self.tr("Please select path for proton prefix")
        )
        self.prefix_layout.addWidget(self.proton_prefix)

    def change_proton(self, i):
        if not self.changeable:
            return
        # First combo box entry: Don't use Proton
        if i == 0:
            self._wrapper_settings.delete_wrapper("proton")
            config_helper.remove_option(self.app_name, "no_wine")
            config_helper.remove_option(f"{self.app_name}.env", "STEAM_COMPAT_DATA_PATH")
            config_helper.remove_option(f"{self.app_name}.env", "STEAM_COMPAT_CLIENT_INSTALL_PATH")

            self.proton_prefix.setEnabled(False)
            # lk: TODO: This has to be fixed properly.
            # lk: It happens because of the widget update. Mask it for now behind disabling the save button

            self._linux_settings.wine_groupbox.setEnabled(True)
        else:
            self.proton_prefix.setEnabled(True)
            self._linux_settings.wine_groupbox.setEnabled(False)
            wrapper = self.possible_proton_combos[i - 1]
            self._wrapper_settings.add_wrapper(wrapper)
            config_helper.add_option(self.app_name, "no_wine", "true")
            config_helper.add_option(
                f"{self.app_name}.env",
                "STEAM_COMPAT_DATA_PATH",
                os.path.expanduser("~/.proton"),
            )
            config_helper.add_option(
                f"{self.app_name}.env",
                "STEAM_COMPAT_CLIENT_INSTALL_PATH",
                str(Path.home().joinpath(".steam", "steam"))
            )

            self.proton_prefix.setText(os.path.expanduser("~/.proton"))

            # Don't use Wine
            self._linux_settings.wine_exec.setText("")
            self._linux_settings.wine_prefix.setText("")

        config_helper.save_config()

    def proton_prefix_edit(self, text: str) -> Tuple[bool, str, str]:
        if not text:
            text = os.path.expanduser("~/.proton")
            return True, text, ""
        parent_dir = os.path.dirname(text)
        return os.path.exists(parent_dir), text, PathEdit.reasons.dir_not_exist

    def proton_prefix_save(self, text: str):
        if not self.changeable:
            return
        config_helper.add_option(
            f"{self.app_name}.env", "STEAM_COMPAT_DATA_PATH", text
        )
        config_helper.save_config()

    def load_settings(self, app_name: str, proton: str):
        self.changeable = False
        self.app_name = app_name
        proton = proton.replace('"', "")
        self.proton_prefix.setEnabled(bool(proton))
        if proton:
            print(proton)
            self.proton_combo.setCurrentText(
                f'"{proton.replace(" run", "")}" run'
            )

        else:
            self.proton_combo.setCurrentIndex(0)

        proton_prefix = self.core.lgd.config.get(
            f"{app_name}.env",
            "STEAM_COMPAT_DATA_PATH",
            fallback=str(Path.home().joinpath(".proton")),
        )
        self.proton_prefix.setText(proton_prefix)
        self.changeable = True

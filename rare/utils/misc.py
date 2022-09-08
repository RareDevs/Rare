import os
import platform
import shlex
import subprocess
import sys
from logging import getLogger
from typing import List, Union

import qtawesome
import requests
from PyQt5.QtCore import (
    pyqtSignal,
    pyqtSlot,
    QObject,
    QRunnable,
    QSettings,
    QStandardPaths,
    QFile,
    QDir,
)
from PyQt5.QtGui import QPalette, QColor, QImage
from PyQt5.QtWidgets import qApp, QStyleFactory
from legendary.models.game import Game
from requests.exceptions import HTTPError

from .models import PathSpec

# Windows

if platform.system() == "Windows":
    # noinspection PyUnresolvedReferences
    from win32com.client import Dispatch  # pylint: disable=E0401

from rare.shared import LegendaryCoreSingleton, ApiResultsSingleton
from rare.utils.paths import image_dir, resources_path

# Mac not supported

from legendary.core import LegendaryCore

logger = getLogger("Utils")
settings = QSettings("Rare", "Rare")

color_role_map = {
    0: "WindowText",
    1: "Button",
    2: "Light",
    3: "Midlight",
    4: "Dark",
    5: "Mid",
    6: "Text",
    7: "BrightText",
    8: "ButtonText",
    9: "Base",
    10: "Window",
    11: "Shadow",
    12: "Highlight",
    13: "HighlightedText",
    14: "Link",
    15: "LinkVisited",
    16: "AlternateBase",
    # 17: "NoRole",
    18: "ToolTipBase",
    19: "ToolTipText",
    20: "PlaceholderText",
    # 21: "NColorRoles",
}

color_group_map = {
    0: "Active",
    1: "Disabled",
    2: "Inactive",
}


def load_color_scheme(path: str) -> QPalette:
    palette = QPalette()
    scheme = QSettings(path, QSettings.IniFormat)
    try:
        scheme.beginGroup("ColorScheme")
        for g in color_group_map:
            scheme.beginGroup(color_group_map[g])
            group = QPalette.ColorGroup(g)
            for r in color_role_map:
                role = QPalette.ColorRole(r)
                color = scheme.value(color_role_map[r], None)
                if color is not None:
                    palette.setColor(group, role, QColor(color))
                else:
                    palette.setColor(group, role, palette.color(QPalette.Active, role))
            scheme.endGroup()
        scheme.endGroup()
    except:
        palette = None
    return palette


def set_color_pallete(color_scheme: str):
    if not color_scheme:
        qApp.setStyle(QStyleFactory.create(qApp.property("rareDefaultQtStyle")))
        qApp.setStyleSheet("")
        qApp.setPalette(qApp.style().standardPalette())
        return
    qApp.setStyle(QStyleFactory.create("Fusion"))
    custom_palette = load_color_scheme(f":/schemes/{color_scheme}")
    if custom_palette is not None:
        qApp.setPalette(custom_palette)
        icon_color = qApp.palette().color(QPalette.Foreground).name()
        qtawesome.set_defaults(color=icon_color)


def get_color_schemes() -> List[str]:
    colors = []
    for file in QDir(":/schemes"):
        colors.append(file)
    return colors


def set_style_sheet(style_sheet: str):
    if not style_sheet:
        qApp.setStyle(QStyleFactory.create(qApp.property("rareDefaultQtStyle")))
        qApp.setStyleSheet("")
        return
    qApp.setStyle(QStyleFactory.create("Fusion"))
    file = QFile(f":/stylesheets/{style_sheet}/stylesheet.qss")
    file.open(QFile.ReadOnly)
    stylesheet = file.readAll().data().decode("utf-8")

    qApp.setStyleSheet(stylesheet)
    icon_color = qApp.palette().color(QPalette.Text).name()
    qtawesome.set_defaults(color="#eeeeee")


def get_style_sheets() -> List[str]:
    styles = []
    for file in QDir(":/stylesheets/"):
        styles.append(file)
    return styles


def get_translations():
    langs = ["en"]
    for i in os.listdir(os.path.join(resources_path, "languages")):
        if i.endswith(".qm") and not i.startswith("qt_"):
            langs.append(i.split(".")[0])
    return langs


def get_latest_version():
    try:
        resp = requests.get(
            "https://api.github.com/repos/Dummerle/Rare/releases/latest"
        )
        tag = resp.json()["tag_name"]
        return tag
    except requests.exceptions.ConnectionError:
        return "0.0.0"


def get_size(b: Union[int, float]) -> str:
    for i in ["", "K", "M", "G", "T", "P", "E"]:
        if b < 1024:
            return f"{b:.2f}{i}B"
        b /= 1024


def get_rare_executable() -> List[str]:
    # lk: detect if nuitka
    if "__compiled__" in globals():
        executable = [sys.executable]
    elif platform.system() == "Linux" or platform.system() == "Darwin":
        # TODO flatpak
        if p := os.environ.get("APPIMAGE"):
            executable = [p]
        else:
            if sys.executable == os.path.abspath(sys.argv[0]):
                executable = [sys.executable]
            else:
                executable = [sys.executable, os.path.abspath(sys.argv[0])]
    elif platform.system() == "Windows":
        executable = [sys.executable]

        if sys.executable != os.path.abspath(sys.argv[0]):
            executable.append(os.path.abspath(sys.argv[0]))

        if executable[0].endswith("python.exe"):
            # be sure to start consoleless then
            executable[0] = executable[0].replace("python.exe", "pythonw.exe")
    else:
        executable = [sys.executable]

    executable[0] = os.path.abspath(executable[0])
    return executable


def create_desktop_link(app_name=None, core: LegendaryCore = None, type_of_link="desktop",
                        for_rare: bool = False) -> bool:
    if not for_rare:
        igame = core.get_installed_game(app_name)

        icon = os.path.join(os.path.join(image_dir(), igame.app_name, "installed.png"))
        icon = icon.replace(".png", "")

    if platform.system() == "Linux":
        if type_of_link == "desktop":
            path = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
        elif type_of_link == "start_menu":
            path = QStandardPaths.writableLocation(QStandardPaths.ApplicationsLocation)
        else:
            return False
        if not os.path.exists(path):
            return False
        executable = get_rare_executable()
        executable = shlex.join(executable)

        if for_rare:
            with open(os.path.join(path, "Rare.desktop"), "w") as desktop_file:
                desktop_file.write(
                    "[Desktop Entry]\n"
                    f"Name=Rare\n"
                    f"Type=Application\n"
                    f"Categories=Game;\n"
                    f"Icon={os.path.join(resources_path, 'images', 'Rare.png')}\n"
                    f"Exec={executable}\n"
                    "Terminal=false\n"
                    "StartupWMClass=Rare\n"
                )
        else:
            with open(os.path.join(path, f"{igame.title}.desktop"), "w") as desktop_file:
                desktop_file.write(
                    "[Desktop Entry]\n"
                    f"Name={igame.title}\n"
                    f"Type=Application\n"
                    f"Categories=Game;\n"
                    f"Icon={icon}.png\n"
                    f"Exec={executable} launch {app_name}\n"
                    "Terminal=false\n"
                    "StartupWMClass=Rare\n"
                )
            os.chmod(os.path.join(path, f"{igame.title}.desktop"), 0o755)

        return True

    elif platform.system() == "Windows":
        # Target of shortcut
        if type_of_link == "desktop":
            target_folder = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
        elif type_of_link == "start_menu":
            target_folder = os.path.join(
                QStandardPaths.writableLocation(QStandardPaths.ApplicationsLocation),
                ".."
            )
        else:
            logger.warning("No valid type of link")
            return False
        if not os.path.exists(target_folder):
            return False

        if for_rare:
            linkName = "Rare.lnk"
        else:
            linkName = igame.title
            # TODO: this conversion is not applied everywhere (see base_installed_widget), should it?
            for c in r'<>?":|\/*':
                linkName = linkName.replace(c, "")

            linkName = f"{linkName.strip()}.lnk"

        # Path to location of link file
        pathLink = os.path.join(target_folder, linkName)

        # Add shortcut
        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(pathLink)

        executable = get_rare_executable()
        arguments = []

        if len(executable) > 1:
            arguments.extend(executable[1:])
        executable = executable[0]

        if not for_rare:
            arguments.extend(["launch", app_name])

        shortcut.Targetpath = executable
        # Maybe there is a better solution, but windows does not accept single quotes (Windows is weird)
        shortcut.Arguments = shlex.join(arguments).replace("'", '"')
        if for_rare:
            shortcut.WorkingDirectory = QStandardPaths.writableLocation(QStandardPaths.HomeLocation)

        # Icon
        if for_rare:
            icon_location = os.path.join(resources_path, "images", "Rare.ico")
        else:
            if not os.path.exists(f"{icon}.ico"):
                img = QImage()
                img.load(f"{icon}.png")
                img.save(f"{icon}.ico")
                logger.info("Created ico file")
            icon_location = f"{icon}.ico"
        shortcut.IconLocation = os.path.abspath(icon_location)

        shortcut.save()
        return True

    # mac OS is based on Darwin
    elif platform.system() == "Darwin":
        return False


class WineResolverSignals(QObject):
    result_ready = pyqtSignal(str)


class WineResolver(QRunnable):
    def __init__(self, path: str, app_name: str):
        super(WineResolver, self).__init__()
        self.signals = WineResolverSignals()
        self.setAutoDelete(True)
        self.wine_env = os.environ.copy()
        core = LegendaryCoreSingleton()
        self.wine_env.update(core.get_app_environment(app_name))
        self.wine_env["WINEDLLOVERRIDES"] = "winemenubuilder=d;mscoree=d;mshtml=d;"
        self.wine_env["DISPLAY"] = ""

        self.wine_binary = core.lgd.config.get(
            app_name,
            "wine_executable",
            fallback=core.lgd.config.get("default", "wine_executable", fallback="wine"),
        )
        self.winepath_binary = os.path.join(
            os.path.dirname(self.wine_binary), "winepath"
        )
        self.path = PathSpec(core, app_name).cook(path)

    @pyqtSlot()
    def run(self):
        if "WINEPREFIX" not in self.wine_env or not os.path.exists(
                self.wine_env["WINEPREFIX"]
        ):
            # pylint: disable=E1136
            self.signals.result_ready[str].emit(str())
            return
        if not os.path.exists(self.wine_binary) or not os.path.exists(
                self.winepath_binary
        ):
            # pylint: disable=E1136
            self.signals.result_ready[str].emit(str())
            return
        path = self.path.strip().replace("/", "\\")
        # lk: if path does not exist form
        cmd = [self.wine_binary, "cmd", "/c", "echo", path]
        # lk: if path exists and needs a case sensitive interpretation form
        # cmd = [self.wine_binary, 'cmd', '/c', f'cd {path} & cd']
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.wine_env,
            shell=False,
            text=True,
        )
        out, err = proc.communicate()
        # Clean wine output
        out = out.strip().strip('"')
        proc = subprocess.Popen(
            [self.winepath_binary, "-u", out],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.wine_env,
            shell=False,
            text=True,
        )
        out, err = proc.communicate()
        real_path = os.path.realpath(out.strip())
        # pylint: disable=E1136
        self.signals.result_ready[str].emit(real_path)
        return


class CloudSignals(QObject):
    result_ready = pyqtSignal(list)  # List[SaveGameFile]


class CloudWorker(QRunnable):
    def __init__(self):
        super(CloudWorker, self).__init__()
        self.signals = CloudSignals()
        self.setAutoDelete(True)
        self.core = LegendaryCoreSingleton()

    def run(self) -> None:
        try:
            result = self.core.get_save_games()
        except HTTPError:
            result = None
        self.signals.result_ready.emit(result)


def get_raw_save_path(game: Game):
    if game.supports_cloud_saves:
        return (
            game.metadata.get("customAttributes", {})
                .get("CloudSaveFolder", {})
                .get("value")
        )


def get_default_platform(app_name):
    api_results = ApiResultsSingleton()
    if platform.system() != "Darwin" or app_name not in api_results.mac_games:
        return "Windows"
    else:
        return "Mac"


def icon(icn_str: str, fallback: str = None, **kwargs):
    try:
        return qtawesome.icon(icn_str, **kwargs)
    except Exception as e:
        if not fallback:
            logger.warning(f"{e} {icn_str}")
    if fallback:
        try:
            return qtawesome.icon(fallback, **kwargs)
        except Exception as e:
            logger.error(str(e))
    if kwargs.get("color"):
        kwargs["color"] = "red"
    return qtawesome.icon("ei.error", **kwargs)

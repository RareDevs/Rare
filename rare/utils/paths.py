import os
import platform
import shlex
import shutil
import sys
from logging import getLogger
from pathlib import Path
from typing import List

from PySide6.QtCore import QStandardPaths

if platform.system() == "Windows":
    # noinspection PyUnresolvedReferences
    from win32com.client import Dispatch  # pylint: disable=E0401

logger = getLogger("Paths")

# This depends on the location of this file (obviously)
resources_path = Path(__file__).absolute().parent.parent.joinpath("resources")

# lk: delete old Rare directories
for old_dir in [
    Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.CacheLocation), "rare").joinpath("tmp"),
    Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation), "rare").joinpath("images"),
    Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.CacheLocation), "rare"),
    Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation), "rare"),
]:
    if old_dir.exists():
        # lk: case-sensitive matching on Winblows
        if old_dir.stem in old_dir.parent.iterdir():
            shutil.rmtree(old_dir, ignore_errors=True)


# lk: TempLocation doesn't depend on OrganizationName or ApplicationName
# lk: so it is fine to use it before initializing the QApplication
def lock_file() -> Path:
    return Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.TempLocation), "Rare.lock")


def config_dir() -> Path:
    # FIXME: This returns ~/.config/Rare/Rare/ for some reason while the settings are in ~/.config/Rare/Rare.conf
    # Take the parent for now, but this should be investigated
    return Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)).parent


def data_dir() -> Path:
    return Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))


def cache_dir() -> Path:
    return Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.CacheLocation))


def image_dir() -> Path:
    return data_dir().joinpath("images")


def image_dir_game(app_name: str) -> Path:
    return image_dir().joinpath(app_name)


def image_tall_path(app_name: str, color: bool = True) -> Path:
    return image_dir_game(app_name).joinpath("tall.png" if color else "tall_gray.png")


def image_wide_path(app_name: str, color: bool = True) -> Path:
    return image_dir_game(app_name).joinpath("wide.png" if color else "wide_gray.png")


def image_icon_path(app_name: str, color: bool = True) -> Path:
    return image_dir_game(app_name).joinpath("icon.png" if color else "icon_gray.png")


def log_dir() -> Path:
    return cache_dir().joinpath("logs")


def tmp_dir() -> Path:
    return cache_dir().joinpath("tmp")


def create_dirs() -> None:
    for path in (data_dir(), cache_dir(), image_dir(), log_dir(), tmp_dir()):
        if not path.exists():
            path.mkdir(parents=True)
            logger.info(f"Created directory at {path}")


def home_dir() -> Path:
    return Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.HomeLocation))


def desktop_dir() -> Path:
    return Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DesktopLocation))


def applications_dir() -> Path:
    return Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.ApplicationsLocation))


def proton_compat_dir(name: str) -> Path:
    if not (compat_dir := data_dir().joinpath(f"compatdata/{name}")).is_dir():
        compat_dir.mkdir(parents=True)
        if not (prefix_dir := compat_dir.joinpath("pfx")).is_dir():
            prefix_dir.mkdir(parents=True)
    return compat_dir


def wine_prefix_dir(name: str) -> Path:
    if not (prefix_dir := proton_compat_dir(name).joinpath("pfx")).is_dir():
        prefix_dir.mkdir(parents=True)
    return prefix_dir


def compat_shaders_dir(name: str) -> Path:
    if not (shader_dir := proton_compat_dir(name).joinpath("cache/shaders")).is_dir():
        shader_dir.mkdir(parents=True)
    return shader_dir


def compat_logs_dir(name: str) -> Path:
    if not (logs_dir := proton_compat_dir(name).joinpath("cache/logs")).is_dir():
        logs_dir.mkdir(parents=True)
    return logs_dir



# fmt: off
__link_suffix = {
    "Windows": {
        "link": "lnk",
        "icon": "ico",
    },
    "FreeBSD": {
        "link": "desktop",
        "icon": "png",
    },
    "Linux": {
        "link": "desktop",
        "icon": "png",
    },
    "Darwin": {
        "link": "",
        "icon": "icns",
    },
}


def desktop_links_supported() -> bool:
    supported_systems = [k for (k, v) in __link_suffix.items() if v["link"]]
    return platform.system() in supported_systems


def desktop_icon_suffix() -> str:
    return __link_suffix[platform.system()]["icon"]


def desktop_icon_path(app_name: str) -> Path:
    return image_dir_game(app_name).joinpath(f"desktop_icon.{desktop_icon_suffix()}")


__link_type = {
    "desktop": desktop_dir(),
    # lk: for some undocumented reason, on Windows we used the parent directory
    # lk: for start menu items. Mirror it here for backwards compatibility
    "start_menu": applications_dir().parent if platform.system() == "Windows" else applications_dir(),
}


def desktop_link_types() -> List:
    return list(__link_type.keys())


# fmt: on


def desktop_link_path(link_name: str, link_type: str) -> Path:
    """
    Creates the path of a shortcut link

    :param link_name:
        Name of the shortcut file
    :param link_type:
        "desktop" or "start_menu"
    :return Path:
        shortcut path
    """
    return __link_type[link_type].joinpath(f"{link_name}.{__link_suffix[platform.system()]['link']}")


def get_rare_executable() -> List[str]:
    logger.debug(f"Trying to find executable: {sys.executable}, {sys.argv}")
    # lk: detect if nuitka
    if "__compiled__" in globals():
        executable = [sys.executable]
    elif sys.argv[0].endswith("__main__.py"):
        executable = [sys.executable, "-m", "rare"]
    elif platform.system() in {"Linux", "FreeBSD", "Darwin"}:
        if p := os.environ.get("APPIMAGE"):
            executable = [p]
        else:
            if sys.executable == os.path.abspath(sys.argv[0]):
                executable = [sys.executable]
            else:
                executable = [os.path.abspath(sys.argv[0])]
    elif platform.system() == "Windows":
        executable = [sys.executable]

        if sys.executable != os.path.abspath(sys.argv[0]):
            executable.append(os.path.abspath(sys.argv[0]))

        if executable[0].endswith("python.exe"):
            # be sure to start console-less then
            executable[0] = executable[0].replace("python.exe", "pythonw.exe")

        if executable[0].endswith("pythonw.exe"):
            if executable[1].endswith("rare"):
                executable[1] = executable[1] + ".exe"
    else:
        executable = [sys.executable]

    executable[0] = os.path.abspath(executable[0])
    return executable


def create_desktop_link(app_name: str, app_title: str = "", link_name: str = "", link_type="desktop") -> bool:
    """
    Creates a desktop or start menu shortcut link

    :param app_name:
        app_name or "rare_shortcut" for Rare itself
    :param app_title:
        the title shown in the shortcut
        (overrides to "Rare" for "rare_shortcut")
    :param link_name:
        the sanitized filename of the shortcut (use the folder_name attribute of RareGame)
        (overrides to "Rare" for "rare_shortcut")
    :param link_type:
        "desktop" or "start_menu"
    :return bool:
        True if successful else False
    """
    # macOS is based on Darwin
    if not desktop_links_supported():
        logger.error(f"Shortcut creation is not available on {platform.system()}")
        return False

    if link_type not in ["desktop", "start_menu"]:
        logger.error(f"Invalid link type {link_type}")
        return False

    for_rare = app_name == "rare_shortcut"

    if for_rare:
        icon_path = resources_path.joinpath("images", f"Rare.{desktop_icon_suffix()}")
        app_title = "Rare"
        link_name = "Rare"
    else:
        icon_path = desktop_icon_path(app_name)
        if not app_title or not link_name:
            logger.error("Missing app_title or link_name")
            return False

    shortcut_path = desktop_link_path(link_name, link_type)
    if not shortcut_path.parent.exists():
        logger.error(f"Parent directory {shortcut_path.parent} does not exist")
        return False
    else:
        logger.info(f"Creating shortcut for {app_title} at {shortcut_path}")

    if platform.system() in {"Linux", "FreeBSD"}:
        executable = get_rare_executable()
        executable = shlex.join(executable)
        if not for_rare:
            executable = f"{executable} launch {app_name}"

        with shortcut_path.open(mode="w") as desktop_file:
            desktop_file.write(
                "[Desktop Entry]\n"
                f"Name={app_title}\n"
                "Type=Application\n"
                "Categories=Game;\n"
                f"Icon={icon_path}\n"
                f"Exec={executable}\n"
                "Terminal=false\n"
                "StartupWMClass=Rare\n"
            )
        # shortcut_path.chmod(0o755)
        return True

    elif platform.system() == "Windows":
        # Add shortcut
        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(shortcut_path))

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

        shortcut.Description = app_title
        if for_rare:
            shortcut.WorkingDirectory = str(home_dir())

        # Icon
        shortcut.IconLocation = str(icon_path.absolute())

        shortcut.save()
        return True

import os
import platform
import shutil
from logging import getLogger
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import asdict

import vdf

from rare.utils.paths import image_icon_path, image_wide_path, image_tall_path, desktop_icon_path, get_rare_executable
from rare.models.steam import SteamUser, SteamShortcut

if platform.system() == "Windows":
    # noinspection PyUnresolvedReferences
    import winreg  # pylint: disable=E0401

logger = getLogger("SteamShortcuts")

steam_client_install_paths = [os.path.expanduser("~/.local/share/Steam")]


def find_steam() -> Optional[str]:
    if platform.system() == "Windows":
        # Find the Steam install directory or raise an error
        try:  # 32-bit
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Valve\\Steams")
        except FileNotFoundError:
            try:  # 64-bit
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Wow6432Node\\Valve\\Steam")
            except FileNotFoundError as e:
                return None
        return winreg.QueryValueEx(key, "InstallPath")[0]
    # return the first valid path
    elif platform.system() in {"Linux", "FreeBSD"}:
        for path in steam_client_install_paths:
            if os.path.isdir(path) and os.path.isfile(os.path.join(path, "steam.sh")):
                return path
    return None


def find_steam_users(steam_path: str) -> List[SteamUser]:
    _users = []
    vdf_path = os.path.join(steam_path, "config", "loginusers.vdf")
    if not os.path.exists(vdf_path):
        return _users
    with open(vdf_path, "r", encoding="utf-8") as f:
        users = vdf.load(f).get("users", {})
    for long_id, user in users.items():
        _users.append(SteamUser(long_id, user))
    return _users


def _load_shortcuts(steam_path: str, user: SteamUser) -> Dict[str, SteamShortcut]:
    _shortcuts = {}
    vdf_path = os.path.join(steam_path, "userdata", str(user.short_id), "config", "shortcuts.vdf")
    if not os.path.exists(vdf_path):
        return _shortcuts
    with open(vdf_path, "rb") as f:
        shortcuts = vdf.binary_load(f).get("shortcuts", {})
    for idx, shortcut in shortcuts.items():
        _shortcuts[idx] = SteamShortcut.from_dict(shortcut)
    return _shortcuts


def _save_shortcuts(steam_path: str, user: SteamUser, shortcuts: Dict[str, SteamShortcut]) -> None:
    _shortcuts = {k: asdict(v) for k, v in shortcuts.items()}
    vdf_path = os.path.join(steam_path, "userdata", str(user.short_id), "config", "shortcuts.vdf")
    with open(vdf_path, "wb") as f:
        vdf.binary_dump({"shortcuts": _shortcuts}, f)


__steam_dir: Optional[str] = None
__steam_user: Optional[SteamUser] = None
__steam_shortcuts: Optional[Dict] = None


def steam_shortcuts_supported() -> bool:
    return __steam_dir is not None and __steam_user is not None and __steam_shortcuts is not None


def load_steam_shortcuts():
    global __steam_shortcuts, __steam_dir, __steam_user

    if __steam_shortcuts is not None:
        return

    steam_dir = find_steam()
    if not steam_dir:
        logger.error("Failed to find Steam install directory")
        return
    __steam_dir = steam_dir

    steam_users = find_steam_users(steam_dir)
    if not steam_users:
        logger.error("Failed to find any Steam users")
        return
    else:
        steam_user = next(
            filter(lambda x: x.most_recent, steam_users),
            sorted(steam_users, key=lambda x: x.last_login, reverse=True)[0]
        )
        logger.info(
            "Found most recently logged-in user %s(%s) (%s)",
            steam_user.account_name, steam_user.persona_name, steam_user.last_login
        )
    __steam_user = steam_user

    __steam_shortcuts = _load_shortcuts(steam_dir, steam_user)


def save_steam_shortcuts():
    logger.info(
        "%s Steam shortcuts for user %s(%s)",
        "Saving" if __steam_shortcuts else "Removing",
        __steam_user.account_name,
        __steam_user.persona_name
    )
    _save_shortcuts(__steam_dir, __steam_user, __steam_shortcuts)


def steam_shortcut_exists(app_name: str) -> bool:
    return SteamShortcut.calculate_appid(app_name) in {s.appid for s in __steam_shortcuts.values()}


def remove_steam_shortcut(app_name: str) -> Optional[SteamShortcut]:
    global __steam_shortcuts

    if not steam_shortcut_exists(app_name):
        logger.error("Game %s doesn't have an associated Steam shortcut", app_name)
        return None

    appid = SteamShortcut.calculate_appid(app_name)
    removed = next(filter(lambda item: item[1].appid == appid, __steam_shortcuts.items()))
    shortcuts = dict(filter(lambda item: item[1].appid != appid, __steam_shortcuts.items()))
    __steam_shortcuts = shortcuts
    return removed[1]


def add_steam_shortcut(app_name: str, app_title: str) -> SteamShortcut:
    global __steam_shortcuts

    if steam_shortcut_exists(app_name):
        logger.info("Removing old Steam shortcut for %s", app_name)
        remove_steam_shortcut(app_name)

    command = get_rare_executable()
    arguments = ["launch", app_name]
    if len(command) > 1:
        arguments = command[1:] + arguments
    shortcut = SteamShortcut.create(
        app_name=app_name,
        app_title=f"{app_title} (Rare)",
        executable=command[0],
        start_dir=os.path.dirname(command[0]),
        icon=desktop_icon_path(app_name).as_posix(),
        launch_options=arguments,
    )

    key = int(max(__steam_shortcuts.keys(), default="0"))
    __steam_shortcuts[str(key+1)] = shortcut
    return shortcut


def add_steam_coverart(app_name: str, shortcut: SteamShortcut):
    steam_grid_dir = os.path.join(__steam_dir, "userdata", str(__steam_user.short_id), "config", "grid")
    if not os.path.exists(steam_grid_dir):
        os.mkdir(steam_grid_dir)
    shutil.copy(image_wide_path(app_name), os.path.join(steam_grid_dir, shortcut.game_hero))
    shutil.copy(image_icon_path(app_name), os.path.join(steam_grid_dir, shortcut.game_logo))
    shutil.copy(image_wide_path(app_name), os.path.join(steam_grid_dir, shortcut.grid_wide))
    shutil.copy(image_tall_path(app_name), os.path.join(steam_grid_dir, shortcut.grid_tall))


def remove_steam_coverart(shortcut: SteamShortcut):
    steam_grid_dir = os.path.join(__steam_dir, "userdata", str(__steam_user.short_id), "config", "grid")
    if not os.path.exists(steam_grid_dir):
        logger.warning("Path does not exist %s", steam_grid_dir)
        return
    Path(steam_grid_dir).joinpath(shortcut.game_hero).unlink(missing_ok=True)
    Path(steam_grid_dir).joinpath(shortcut.game_logo).unlink(missing_ok=True)
    Path(steam_grid_dir).joinpath(shortcut.grid_wide).unlink(missing_ok=True)
    Path(steam_grid_dir).joinpath(shortcut.grid_tall).unlink(missing_ok=True)


if __name__ == "__main__":

    from pprint import pprint

    load_steam_shortcuts()

    print(__steam_dir)
    print(__steam_user)
    print(__steam_shortcuts)

    def print_shortcuts():
        for k, s in __steam_shortcuts.items():
            print({k: asdict(s)})
            print(vars(s))
        print()

    print_shortcuts()

    add_steam_shortcut("test1", "Test1")
    add_steam_shortcut("test2", "Test2")
    add_steam_shortcut("test3", "Test3")
    add_steam_shortcut("test1", "Test1")

    remove_steam_shortcut("test2")

    print_shortcuts()

import os
import platform
import shutil
from logging import getLogger
from typing import Optional, List, Dict

import vdf

from rare.models.steam import SteamUser, SteamShortcut

logger = getLogger("SteamShortcuts")

steam_client_install_paths = [os.path.expanduser("~/.local/share/Steam")]


def find_steam() -> Optional[str]:
    # return the first valid path
    if platform.system() in {"Linux", "FreeBSD"}:
        for path in steam_client_install_paths:
            if os.path.isdir(path) and os.path.isfile(os.path.join(path, "steam.sh")):
                return path
    return None


def find_users(steam_path: str) -> List[SteamUser]:
    _users = []
    vdf_path = os.path.join(steam_path, "config", "loginusers.vdf")
    with open(vdf_path, 'r') as f:
        users = vdf.load(f).get("users", {})
    for long_id, user in users.items():
        _users.append(SteamUser(long_id, user))
    return _users


def load_shortcuts(steam_path: str, user: SteamUser) -> Dict[str, SteamShortcut]:
    _shortcuts = {}
    vdf_path = os.path.join(steam_path, "userdata", str(user.short_id), "config", "shortcuts.vdf")
    with open(vdf_path, 'rb') as f:
        shortcuts = vdf.binary_load(f).get("shortcuts", {})
    for idx, shortcut in shortcuts.items():
        _shortcuts[idx] = SteamShortcut.from_dict(shortcut)
    return _shortcuts


def save_shortcuts(steam_path: str, user: SteamUser, shortcuts: Dict[str, Dict]) -> None:
    vdf_path = os.path.join(steam_path, "userdata", str(user.short_id), "config", "shortcuts.vdf")
    with open(vdf_path, 'wb') as f:
        vdf.binary_dump({"shortcuts": shortcuts}, f)


if __name__ == "__main__":

    from pprint import pprint
    from dataclasses import asdict

    steam_dir = find_steam()

    users = find_users(steam_dir)
    print(users)

    user = next(filter(lambda x: x.most_recent, users))
    print(user)
    print()

    shortcuts = load_shortcuts(steam_dir, user)
    for k, s in shortcuts.items():
        print(asdict(s))
        print(vars(s))
        print()

    def image_path(app_name: str, image: str) -> str:
        return f"/home/loathingkernel/.local/share/Rare/Rare/images/{app_name}/{image}"

    test_shc = SteamShortcut.create(
        app_name="18fafa2d70d64831ab500a9d65ba9ab8",
        app_title="Crying Suns (Rare Test)",
        executable="/usr/bin/rare",
        start_dir="/usr/bin",
        icon=image_path("18fafa2d70d64831ab500a9d65ba9ab8", "icon.png"),
        launch_options=["launch", "18fafa2d70d64831ab500a9d65ba9ab8"]
    )
    print(asdict(test_shc))
    print(vars(test_shc))
    test_vdf = vdf.binary_dumps(asdict(test_shc))
    print(vdf.binary_loads(test_vdf))

    save_shortcuts(steam_dir, user, {"0": asdict(test_shc)})

    steam_grid_dir = os.path.join(steam_dir, "userdata", str(user.short_id), "config", "grid")
    shutil.copy(
        image_path("18fafa2d70d64831ab500a9d65ba9ab8", "card_installed.png"),
        os.path.join(steam_grid_dir, test_shc.game_hero)
    )
    shutil.copy(
        image_path("18fafa2d70d64831ab500a9d65ba9ab8", "icon.png"),
        os.path.join(steam_grid_dir, test_shc.game_logo)
    )
    shutil.copy(
        image_path("18fafa2d70d64831ab500a9d65ba9ab8", "card_installed.png"),
        os.path.join(steam_grid_dir, test_shc.grid_wide)
    )
    shutil.copy(
        image_path("18fafa2d70d64831ab500a9d65ba9ab8", "card_installed.png"),
        os.path.join(steam_grid_dir, test_shc.grid_tall)
    )

    shortcuts = load_shortcuts(steam_dir, user)
    print(shortcuts)

import platform
import binascii
import shlex
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Type, Any


class SteamUser:
    def __init__(self, long_id: str, user: Dict):
        super(SteamUser, self).__init__()
        self._long_id: str = long_id
        self._user = user.copy()

    @property
    def long_id(self) -> int:
        return int(self._long_id)

    @property
    def short_id(self) -> int:
        return self.long_id & 0xFFFFFFFF

    @property
    def account_name(self) -> str:
        return self._user.get("AccountName", "")

    @property
    def persona_name(self) -> str:
        return self._user.get("PersonaName", "")

    @property
    def most_recent(self) -> bool:
        return bool(int(self._user.get("MostRecent", "0")))

    @property
    def last_login(self) -> datetime:
        return datetime.fromtimestamp(float(self._user.get("Timestamp", "0")), timezone.utc)

    @property
    def __dict__(self):
        return dict(
            long_id=self.long_id,
            short_id=self.short_id,
            account_name=self.account_name,
            persona_name=self.persona_name,
            most_recent=self.most_recent,
            last_login=self.last_login,
        )

    def __repr__(self):
        return repr(vars(self))


@dataclass
class SteamShortcut:

    appid: int
    AppName: str
    Exe: str
    StartDir: str
    icon: str
    ShortcutPath: str
    LaunchOptions: str
    IsHidden: bool
    AllowDesktopConfig: bool
    AllowOverlay: bool
    OpenVR: bool
    Devkit: bool
    DevkitGameID: str
    DevkitOverrideAppID: int
    LastPlayTime: int
    FlatpakAppID: str
    tags: Dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["SteamShortcut"], src: Dict[str, Any]) -> "SteamShortcut":
        d = src.copy()
        tmp = cls(
            appid=d.pop("appid", 0),
            AppName=d.pop("AppName", ""),
            Exe=d.pop("Exe", ""),
            StartDir=d.pop("StartDir", ""),
            icon=d.pop("icon", ""),
            ShortcutPath=d.pop("ShortcutPath", ""),
            LaunchOptions=d.pop("LaunchOptions", ""),
            IsHidden=bool(d.pop("IsHidden", 0)),
            AllowDesktopConfig=bool(d.pop("AllowDesktopConfig", 1)),
            AllowOverlay=bool(d.pop("AllowOverlay", 1)),
            OpenVR=bool(d.pop("OpenVR", 0)),
            Devkit=bool(d.pop("Devkit", 0)),
            DevkitGameID=d.pop("DevkitGameID", ""),
            DevkitOverrideAppID=d.pop("DevkitOverrideAppID", 0),
            LastPlayTime=d.pop("LastPlayTime", 0),
            FlatpakAppID=d.pop("FlatpakAppID", ""),
            tags=d.pop("tags", {}),
        )
        return tmp

    @classmethod
    def create(
        cls: Type["SteamShortcut"],
        app_name: str,
        app_title: str,
        executable: str,
        start_dir: str,
        icon: str,
        launch_options: List[str],
    ) -> "SteamShortcut":
        shortcut = cls.from_dict({})
        shortcut.appid = cls.calculate_appid(app_name)
        shortcut.AppName = app_title
        shortcut.Exe = executable if platform.system() == "Windows" else shlex.quote(executable)
        shortcut.StartDir = start_dir
        shortcut.icon = icon
        shortcut.LaunchOptions = shlex.join(launch_options)
        return shortcut

    @staticmethod
    def calculate_appid(app_name) -> int:
        key = "rare_steam_shortcut_" + app_name
        top = binascii.crc32(str.encode(key, "utf-8")) | 0x80000000
        return (((top << 32) | 0x02000000) >> 32) - 0x100000000

    def shortcut_appid(self) -> int:
        return self.appid

    def coverart_appid(self) -> int:
        return self.shortcut_appid() + 0x100000000

    @property
    def grid_wide(self) -> str:
        return f"{self.coverart_appid()}.png"

    @property
    def grid_tall(self) -> str:
        return f"{self.coverart_appid()}p.png"

    @property
    def game_hero(self) -> str:
        return f"{self.coverart_appid()}_hero.png"

    @property
    def game_logo(self) -> str:
        return f"{self.coverart_appid()}_logo.png"

    @property
    def last_played(self):
        return datetime.fromtimestamp(float(self.LastPlayTime), timezone.utc)

    @property
    def __dict__(self):
        ret = dict(
            shortcut_appid=self.shortcut_appid(), grid_appid=self.coverart_appid(), last_played=self.last_played
        )
        return ret

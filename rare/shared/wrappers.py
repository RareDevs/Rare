import json
import os
from logging import getLogger
import shlex
from typing import List, Dict, Iterable, Union, Tuple, Set
from rare.utils import config_helper as config

from PySide6.QtCore import QSettings

from rare.lgndr.core import LegendaryCore
from rare.models.wrapper import Wrapper, WrapperType
from rare.utils.paths import config_dir

logger = getLogger("Wrappers")


class WrapperEntry:
    def __init__(self, checksum: str, enabled: bool = True):
        self.__checksum: str = checksum
        self.__enabled: bool = enabled

    @property
    def checksum(self) -> str:
        return self.__checksum

    @property
    def enabled(self) -> bool:
        return self.__enabled

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(checksum=data.get("checksum"), enabled=data.get("enabled", True))

    @property
    def __dict__(self):
        return dict(checksum=self.__checksum, enabled=self.__enabled)

    # def __eq__(self, other) -> bool:
    #     return self.checksum == other.checksum


class Wrappers:
    def __init__(self):
        self._file = os.path.join(config_dir(), "wrappers.json")
        self._wrappers_dict = {}
        try:
            with open(self._file, "r", encoding="utf-8") as f:
                self._wrappers_dict = json.load(f)
        except FileNotFoundError:
            logger.info("%s does not exist", self._file)
        except json.JSONDecodeError:
            logger.warning("%s is corrupt", self._file)

        self._version = self._wrappers_dict.get("version", 1)

        self._wrappers: Dict[str, Wrapper] = {}
        for wrap_id, wrapper in self._wrappers_dict.get("wrappers", {}).items():
            self._wrappers.update({wrap_id: Wrapper.from_dict(wrapper)})

        self._applists: Dict[str, List[WrapperEntry]] = {}
        for app_name, wrapper_list in self._wrappers_dict.get("applists", {}).items():
            if all(isinstance(x, str) for x in wrapper_list):
                wlist = [WrapperEntry(y) for y in wrapper_list]
            elif all(isinstance(x, dict) for x in wrapper_list):
                wlist = [WrapperEntry.from_dict(y) for y in wrapper_list]
            else:
                wlist = []
            self._applists.update({app_name: wlist})

        # set current file version
        self._version = 2

    def import_wrappers(self, core: LegendaryCore, settings: QSettings, app_names: List):
        for app_name in app_names:
            wrappers = self.get_wrappers(app_name)
            if not wrappers and (commands := settings.value(f"{app_name}/wrapper", [], type=list)):
                logger.info("Importing wrappers from Rare's config")
                settings.remove(f"{app_name}/wrapper")
                for command in commands:
                    wrapper = Wrapper(command=shlex.split(command))
                    wrappers.append(wrapper)
                    self.set_wrappers(app_name, wrappers)
                    logger.debug("Imported previous wrappers in %s Rare: %s", app_name, wrapper.name)

            # NOTE: compatibility with Legendary
            # No Rare settings wrappers, but legendary config wrappers, for backwards compatibility
            if not wrappers and (command := core.lgd.config.get(app_name, "wrapper", fallback="")):
                logger.info("Importing wrappers from legendary's config")
                wrapper = Wrapper(
                    command=shlex.split(command),
                    name="Imported from Legendary",
                    wtype=WrapperType.LEGENDARY_IMPORT
                )
                wrappers = [wrapper]
                self.set_wrappers(app_name, wrappers)
                logger.debug("Imported existing wrappers in %s legendary: %s", app_name, wrapper.name)

    @property
    def user_wrappers(self) -> Iterable[Wrapper]:
        return filter(lambda w: w.is_editable, self._wrappers.values())
        # for wrap in self.__wrappers.values():
        #     if wrap.is_user_defined:
        #         yield wrap

    def wrapper_command(self, app_name: str) -> str:
        commands = [wrapper.as_str for wrapper in self.get_wrappers(app_name) if wrapper.is_enabled]
        return " ".join(commands)

    def get_checksums(self, app_name: str) -> Set[str]:
        return {entry.checksum for entry in self._applists.get(app_name, [])}

    def get_wrappers(self, app_name: str) -> List[Wrapper]:
        wrappers = []
        for entry in self._applists.get(app_name, []):
            if wrap := self._wrappers.get(entry.checksum, None):
                wrap.is_enabled = entry.enabled
                wrappers.append(wrap)
        return wrappers

    def set_wrappers(self, app_name: str, wrappers: List[Wrapper]) -> None:
        _wrappers = sorted(wrappers, key=lambda w: w.is_compat_tool)
        for w in _wrappers:
            if (md5sum := w.checksum) in self._wrappers.keys():
                if w != self._wrappers[md5sum]:
                    logger.error("Equal csum for unequal wrappers %s, %s", w.name, self._wrappers[md5sum].name)
                if w.is_compat_tool:
                    self._wrappers.update({md5sum: w})
            else:
                self._wrappers.update({md5sum: w})
        self._applists[app_name] = [WrapperEntry(w.checksum, w.is_enabled) for w in _wrappers]
        self.__save_config(app_name)
        self.__save_wrappers()

    def __save_config(self, app_name: str):
        command = self.wrapper_command(app_name)
        config.adjust_option(app_name, "wrapper", command)

    def __save_wrappers(self):
        existing = {csum for csum in self._wrappers.keys()}
        in_use = {entry.checksum for wrappers in self._applists.values() for entry in wrappers}

        for redudant in existing.difference(in_use):
            del self._wrappers[redudant]

        self._wrappers_dict["version"] = self._version
        self._wrappers_dict["wrappers"] = self._wrappers
        self._wrappers_dict["applists"] = self._applists

        with open(os.path.join(self._file), "w+", encoding="utf-8") as f:
            json.dump(self._wrappers_dict, f, default=lambda o: vars(o), indent=2)


if __name__ == "__main__":
    from pprint import pprint
    from argparse import Namespace

    from rare.utils.compat import steam

    global config_dir
    config_dir = os.getcwd
    global config
    config = Namespace()
    config.set_option = lambda x, y, z: print("set_option:", x, y, z)
    config.remove_option = lambda x, y: print("remove_option:", x, y)
    config.save_config = lambda: print("save_config:")
    config.save_option = lambda x, y, z: print("save_option:", x, y, z)

    wr = Wrappers()

    w1 = Wrapper(command=["/usr/bin/w1"], wtype=WrapperType.NONE)
    w2 = Wrapper(command=["/usr/bin/w2"], wtype=WrapperType.COMPAT_TOOL)
    w3 = Wrapper(command=["/usr/bin/w3"], wtype=WrapperType.USER_DEFINED, enabled=False)
    w4 = Wrapper(command=["/usr/bin/w4"], wtype=WrapperType.USER_DEFINED)
    wr.set_wrappers("testgame", [w1, w2, w3, w4])

    w5 = Wrapper(command=["/usr/bin/w5"], wtype=WrapperType.COMPAT_TOOL)
    wr.set_wrappers("testgame2", [w2, w1, w5])

    w6 = Wrapper(command=["/usr/bin/w 6", "-w", "-t"], wtype=WrapperType.USER_DEFINED)
    wr.set_wrappers("testgame", [w1, w2, w3, w6])

    w7 = Wrapper(command=["/usr/bin/w2"], wtype=WrapperType.COMPAT_TOOL)
    app_wrappers = wr.get_wrappers("testgame")
    pprint([w.as_str for w in app_wrappers])
    # item = next(item for item in app_wrappers if item.checksum == w3.checksum)
    app_wrappers.remove(w3)
    wr.set_wrappers("testgame", app_wrappers)

    game_wrappers = wr.get_wrappers("testgame")
    pprint([w.as_str for w in game_wrappers])
    game_wrappers = wr.get_wrappers("testgame2")
    pprint([w.as_str for w in game_wrappers])

    for i, tool in enumerate(steam.find_tools()):
        wt = Wrapper(command=tool.command(), name=tool.name, wtype=WrapperType.COMPAT_TOOL)
        wr.set_wrappers(f"compat_game_{i}", [wt])
        print(wt.as_str)

    for wrp in wr.user_wrappers:
        pprint(wrp.as_str)

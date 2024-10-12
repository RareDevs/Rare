import json
import os
from logging import getLogger
import shlex
from typing import List, Dict, Iterable
from rare.utils import config_helper as config

from PySide6.QtCore import QSettings

from rare.lgndr.core import LegendaryCore
from rare.models.wrapper import Wrapper, WrapperType
from rare.utils.paths import config_dir

logger = getLogger("Wrappers")


class Wrappers:
    def __init__(self):
        self.__file = os.path.join(config_dir(), "wrappers.json")
        self.__wrappers_dict = {}
        try:
            with open(self.__file, "r", encoding="utf-8") as f:
                self.__wrappers_dict = json.load(f)
        except FileNotFoundError:
            logger.info("%s does not exist", self.__file)
        except json.JSONDecodeError:
            logger.warning("%s is corrupt", self.__file)

        self.__wrappers: Dict[str, Wrapper] = {}
        for wrap_id, wrapper in self.__wrappers_dict.get("wrappers", {}).items():
            self.__wrappers.update({wrap_id: Wrapper.from_dict(wrapper)})

        self.__applists: Dict[str, List[str]] = {}
        for app_name, wrapper_list in self.__wrappers_dict.get("applists", {}).items():
            self.__applists.update({app_name: wrapper_list})

    def import_wrappers(self, core: LegendaryCore, settings: QSettings, app_names: List):
        for app_name in app_names:
            wrappers = self.get_game_wrapper_list(app_name)
            if not wrappers and (commands := settings.value(f"{app_name}/wrapper", [], list)):
                logger.info("Importing wrappers from Rare's config")
                settings.remove(f"{app_name}/wrapper")
                for command in commands:
                    wrapper = Wrapper(command=shlex.split(command))
                    wrappers.append(wrapper)
                    self.set_game_wrapper_list(app_name, wrappers)
                    logger.debug("Imported previous wrappers in %s Rare: %s", app_name, wrapper.name)

            # NOTE: compatibility with Legendary
            if not wrappers and (command := core.lgd.config.get(app_name, "wrapper", fallback="")):
                logger.info("Importing wrappers from legendary's config")
                # no qt wrapper, but legendary wrapper, to have backward compatibility
                # pattern = re.compile(r'''((?:[^ "']|"[^"]*"|'[^']*')+)''')
                # wrappers = pattern.split(command)[1::2]
                wrapper = Wrapper(
                    command=shlex.split(command),
                    name="Imported from Legendary",
                    wtype=WrapperType.LEGENDARY_IMPORT
                )
                wrappers = [wrapper]
                self.set_game_wrapper_list(app_name, wrappers)
                logger.debug("Imported existing wrappers in %s legendary: %s", app_name, wrapper.name)

    @property
    def user_wrappers(self) -> Iterable[Wrapper]:
        return filter(lambda w: w.is_editable, self.__wrappers.values())
        # for wrap in self.__wrappers.values():
        #     if wrap.is_user_defined:
        #         yield wrap

    def get_game_wrapper_string(self, app_name: str) -> str:
        commands = [wrapper.as_str for wrapper in self.get_game_wrapper_list(app_name)]
        return " ".join(commands)

    def get_game_wrapper_list(self, app_name: str) -> List[Wrapper]:
        _wrappers = []
        for wrap_id in self.__applists.get(app_name, []):
            if wrap := self.__wrappers.get(wrap_id, None):
                _wrappers.append(wrap)
        return _wrappers

    def get_game_md5sum_list(self, app_name: str) -> List[str]:
        return self.__applists.get(app_name, [])

    def set_game_wrapper_list(self, app_name: str, wrappers: List[Wrapper]) -> None:
        _wrappers = sorted(wrappers, key=lambda w: w.is_compat_tool)
        for w in _wrappers:
            if (md5sum := w.checksum) in self.__wrappers.keys():
                if w != self.__wrappers[md5sum]:
                    logger.error(
                        "Non-unique md5sum for different wrappers %s, %s",
                        w.name,
                        self.__wrappers[md5sum].name,
                    )
                if w.is_compat_tool:
                    self.__wrappers.update({md5sum: w})
            else:
                self.__wrappers.update({md5sum: w})
        self.__applists[app_name] = [w.checksum for w in _wrappers]
        self.__save_config(app_name)
        self.__save_wrappers()

    def __save_config(self, app_name: str):
        command_string = self.get_game_wrapper_string(app_name)
        config.save_option(app_name, "wrapper", command_string)

    def __save_wrappers(self):
        existing = {wrap_id for wrap_id in self.__wrappers.keys()}
        in_use = {wrap_id for wrappers in self.__applists.values() for wrap_id in wrappers}

        for redudant in existing.difference(in_use):
            del self.__wrappers[redudant]

        self.__wrappers_dict["wrappers"] = self.__wrappers
        self.__wrappers_dict["applists"] = self.__applists

        with open(os.path.join(self.__file), "w+", encoding="utf-8") as f:
            json.dump(self.__wrappers_dict, f, default=lambda o: vars(o), indent=2)


if __name__ == "__main__":
    from pprint import pprint
    from argparse import Namespace

    from rare.utils.compat import steam

    global config_dir
    config_dir = os.getcwd
    global config
    config = Namespace()
    config.set_option = lambda x, y, z: print(x, y, z)
    config.remove_option = lambda x, y: print(x, y)
    config.save_config = lambda: print()

    wr = Wrappers()

    w1 = Wrapper(command=["/usr/bin/w1"], wtype=WrapperType.NONE)
    w2 = Wrapper(command=["/usr/bin/w2"], wtype=WrapperType.COMPAT_TOOL)
    w3 = Wrapper(command=["/usr/bin/w3"], wtype=WrapperType.USER_DEFINED)
    w4 = Wrapper(command=["/usr/bin/w4"], wtype=WrapperType.USER_DEFINED)
    wr.set_game_wrapper_list("testgame", [w1, w2, w3, w4])

    w5 = Wrapper(command=["/usr/bin/w5"], wtype=WrapperType.COMPAT_TOOL)
    wr.set_game_wrapper_list("testgame2", [w2, w1, w5])

    w6 = Wrapper(command=["/usr/bin/w 6", "-w", "-t"], wtype=WrapperType.USER_DEFINED)
    wr.set_game_wrapper_list("testgame", [w1, w2, w3, w6])

    w7 = Wrapper(command=["/usr/bin/w2"], wtype=WrapperType.COMPAT_TOOL)
    wrs = wr.get_game_wrapper_list("testgame")
    wrs.remove(w7)
    wr.set_game_wrapper_list("testgame", wrs)

    game_wrappers = wr.get_game_wrapper_list("testgame")
    pprint(game_wrappers)
    game_wrappers = wr.get_game_wrapper_list("testgame2")
    pprint(game_wrappers)

    for i, tool in enumerate(steam.find_tools()):
        wt = Wrapper(command=tool.command(), name=tool.name, wtype=WrapperType.COMPAT_TOOL)
        wr.set_game_wrapper_list(f"compat_game_{i}", [wt])
        print(wt.as_str)

    for wrp in wr.user_wrappers:
        pprint(wrp)

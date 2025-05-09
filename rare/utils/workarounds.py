import platform
from typing import Dict, Set, Union

from PySide6.QtWidgets import QApplication

from rare.utils import config_helper as config

__os_compat: Set = {"Linux", "Darwin", "FreeBSD"}
__os_native: Set = {"Windows"}
__os_all: Set = {*__os_compat, *__os_native}


def __screen_height() -> int:
    return QApplication.instance().primaryScreen().geometry().height()


def __screen_width() -> int:
    return QApplication.instance().primaryScreen().geometry().width()

# Keeps a dictionary of workarounds.
# Can use the following placeholders: res_width, res_height
__workarounds: Dict[str, Dict[str, Dict[str, Dict[str, Union[str, Set]]]]] = {
    # XCOM2
    "3be3c4d681bc46b3b8b26c5df3ae0a18": {
        "options": {
            "override_exe": {
                "value": "Binaries/Win64/XCom2.exe",
                "os": __os_all,
            },
        },
    },
    # Civilization VI
    "Kinglet": {
        "options": {
            "override_exe": {
                "value": "Base/Binaries/Win64EOS/CivilizationVI.exe",
                "os": __os_all,
            },
        },
    },
    # Bioshock 2 Remastered
    "b22ce34b4ce0408c97a888554447479b": {
        "options": {
            "override_exe": {
                "value": "Build/FinalEpic/Bioshock2HD.exe",
                "os": __os_all,
            },
        },
    },
    # Bioshock 1 Remastered
    "bc2c95c6ff564a16b26644f1d3ac3c55": {
        "options": {
            "override_exe": {
                "value": "Build/FinalEpic/BioshockHD.exe",
                "os": __os_all,
            },
        },
    },
    # Eternal Threads
    "ff1d9bf6b1304cb9a12b8754afa78ae5": {
        "options": {
            "override_exe": {
                "value": "EternalThreads.exe",
                "os": __os_compat,
            },
        },
    },
    # Celeste
    "Salt": {
        "options": {
            "start_params": {
                "value": "/gldevice:OpenGL",
                "os": __os_compat,
            },
        },
    },
    # Borderlands: The Pre Sequel
    "Turkey": {
        "options": {
            "start_params": {
                "value": "-NoLauncher",
                "os": __os_compat,
            },
        },
    },
    # Borderlands 2
    "Dodo": {
        "options": {
            "start_params": {
                "value": "-NoLauncher",
                "os": __os_compat,
            },
            # "override_exe": { "value": "Binaries/Win32/Borderlands2.exe", "os": __os_compat, },
        },
    },
    # Tiny Tina's Assault on Dragon Keep: A Wonderlands One shot Adventure
    "9e296d276ad447108f12c654c3341d59": {
        "options": {
            "start_params": {
                "value": "-NoLauncher",
                "os": __os_compat,
            },
        },
    },
    # Brothers: A Tale of Two Sons
    "Tamarind": {
        "options": {
            "start_params": {
                # value set at runtime
                "value": "ResX={res_width} ResY={res_height} -nomovies -nosplash",
                "os": __os_compat,
            },
            "override_exe": {
                "value": "Binaries/Win32/Brothers.exe",
                "os": __os_compat,
            },
        },
    },
    # Borderlands: The Pre Sequel
    "9c203b6ed35846e8a4a9ff1e314f6593": {
        "options": {
            "start_params": {
                "value": "/autorun /ed /autoquit",
                "os": __os_compat,
            },
        },
    },
    # F1® Manager 2024
    "03c9fe3b2869452ba8433ee7708a3e93": {
        "options": {
            "override_exe": {
                "value": "F1Manager24/Binaries/Win64/F1Manage",
                "os": __os_all,
            },
        },
    },
    # Cities Skylines
    "bcbc03d8812a44c18f41cf7d5f849265": {
        "options": {
            "override_exe": {
                "value": "Cities.exe",
                "os": __os_all,
            },
        },
    },
}


def __subst(text: str) -> str:
    return text.format(
        res_width=__screen_width(),
        res_height=__screen_height(),
    )


def apply_workarounds(app_name: str):
    if workaround := __workarounds.get(app_name):
        # apply options
        for opt in (options := workaround.get("options", {})):
            if config.get_option(app_name, opt, None) is not None:
                continue
            if platform.system() not in options[opt].get("os", set()):
                continue
            config.set_option(app_name, opt, __subst(options[opt]["value"]))
        # apply environment
        for var in (environ := workaround.get("environ", {})):
            if config.get_envvar(app_name, var, None) is not None:
                continue
            if platform.system() not in environ[var].get("os", set()):
                continue
            config.set_envvar(app_name, var, __subst(environ[var]["value"]))


__all__ = ["apply_workarounds"]

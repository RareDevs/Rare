from dataclasses import dataclass
from multiprocessing import Queue
from typing import Callable, List, Optional

from .api_monkeys import get_boolean_choice, LgndrIndirectStatus

"""
@dataclass(kw_only=True)
class LgndrCommonArgs:
    # keep this here for future reference
    # when we move to 3.10 we can use 'kw_only' to do dataclass inheritance
    app_name: str
    platform: str = "Windows"
    yes: bool = False
"""


@dataclass
class LgndrImportGameArgs:
    app_path: str
    app_name: str
    platform: str = "Windows"
    disable_check: bool = False
    skip_dlcs: bool = False
    with_dlcs: bool = False
    yes: bool = False
    # Rare: Extra arguments
    indirect_status: LgndrIndirectStatus = LgndrIndirectStatus()
    get_boolean_choice: Callable[[str, bool], bool] = lambda prompt, default=True: default


@dataclass
class LgndrUninstallGameArgs:
    app_name: str
    keep_files: bool = False
    yes: bool = False
    # Rare: Extra arguments
    indirect_status: LgndrIndirectStatus = LgndrIndirectStatus()
    get_boolean_choice: Callable[[str, bool], bool] = lambda prompt, default=True: default


@dataclass
class LgndrVerifyGameArgs:
    app_name: str
    # Rare: Extra arguments
    indirect_status: LgndrIndirectStatus = LgndrIndirectStatus()
    verify_stdout: Callable[[int, int, float, float], None] = lambda a0, a1, a2, a3: print(
        f"Verification progress: {a0}/{a1} ({a2:.01f}%) [{a3:.1f} MiB/s]\t\r"
    )


@dataclass
class LgndrInstallGameArgs:
    app_name: str
    base_path: str = ""
    shared_memory: int = 0
    max_workers: int = 0
    force: bool = False
    disable_patching: bool = False
    game_folder: str = ""
    override_manifest: str = ""
    override_old_manifest: str = ""
    override_base_url: str = ""
    platform: str = "Windows"
    file_prefix: List = None
    file_exclude_prefix: List = None
    install_tag: Optional[List[str]] = None
    order_opt: bool = False
    dl_timeout: int = 10
    repair_mode: bool = False
    repair_and_update: bool = False
    disable_delta: bool = False
    override_delta_manifest: str = ""
    egl_guid: str = ""
    preferred_cdn: str = None
    no_install: bool = False
    ignore_space: bool = False
    disable_sdl: bool = False
    reset_sdl: bool = False
    skip_sdl: bool = False
    disable_https: bool = False
    yes: bool = True
    # Rare: Extra arguments
    indirect_status: LgndrIndirectStatus = LgndrIndirectStatus()
    get_boolean_choice: Callable[[str, bool], bool] = lambda prompt, default=True: default
    sdl_prompt: Callable[[str, str], List[str]] = lambda sdl_data, title: [""]
    verify_stdout: Callable[[int, int, float, float], None] = lambda a0, a1, a2, a3: print(
        f"Verification progress: {a0}/{a1} ({a2:.01f}%) [{a3:.1f} MiB/s]\t\r"
    )
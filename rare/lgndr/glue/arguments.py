from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional, Dict

from rare.lgndr.glue.monkeys import (
    LgndrIndirectStatus,
    GetBooleanChoiceProtocol,
    SdlPromptProtocol,
    VerifyStdoutProtocol,
    UiUpdateProtocol,
    get_boolean_choice_factory,
    sdl_prompt_factory,
    verify_stdout_factory,
    ui_update_factory,
    DLManagerSignals,
)

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
    indirect_status: LgndrIndirectStatus = field(default_factory=LgndrIndirectStatus)
    get_boolean_choice: GetBooleanChoiceProtocol = get_boolean_choice_factory(True)


@dataclass
class LgndrUninstallGameArgs:
    app_name: str
    keep_files: bool = False
    skip_uninstaller: bool = False
    yes: bool = False
    # Rare: Extra arguments
    indirect_status: LgndrIndirectStatus = field(default_factory=LgndrIndirectStatus)
    get_boolean_choice_main: GetBooleanChoiceProtocol = get_boolean_choice_factory(True)
    get_boolean_choice_handler: GetBooleanChoiceProtocol = get_boolean_choice_factory(True)


@dataclass
class LgndrVerifyGameArgs:
    app_name: str
    # Rare: Extra arguments
    indirect_status: LgndrIndirectStatus = field(default_factory=LgndrIndirectStatus)
    verify_stdout: VerifyStdoutProtocol = verify_stdout_factory(None)


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
    bind_ip: str = ""
    # FIXME: move to LgndrInstallGameRealArgs
    skip_dlcs: bool = False
    with_dlcs: bool = False
    # end of FIXME
    yes: bool = True
    # Rare: Extra arguments
    indirect_status: LgndrIndirectStatus = field(default_factory=LgndrIndirectStatus)
    get_boolean_choice: GetBooleanChoiceProtocol = get_boolean_choice_factory(True)
    verify_stdout: VerifyStdoutProtocol = verify_stdout_factory(None)

    def __post_init__(self):
        self.sdl_prompt: SdlPromptProtocol = sdl_prompt_factory(self.install_tag)


@dataclass
class LgndrInstallGameRealArgs:
    app_name: str
    platform: str = "Windows"
    repair_mode: bool = False
    repair_file: str = ""
    no_install: bool = False
    save_path: str = ""
    skip_dlcs: bool = False
    with_dlcs: bool = False
    dlm_debug: bool = False
    yes: bool = False
    # Rare: Extra arguments
    install_prereqs: bool = False
    indirect_status: LgndrIndirectStatus = field(default_factory=LgndrIndirectStatus)
    ui_update: UiUpdateProtocol = ui_update_factory(None)
    dlm_signals: DLManagerSignals = field(default_factory=DLManagerSignals)


@dataclass
class LgndrInstallGameRealRet:
    class ReturnCode(IntEnum):
        ERROR = 1
        STOPPED = 2
        FINISHED = 3

    app_name: str
    ret_code: ReturnCode = ReturnCode.ERROR
    message: str = ""
    dlcs: Optional[List[Dict]] = None
    sync_saves: bool = False
    tip_url: str = ""
    shortcuts: bool = False

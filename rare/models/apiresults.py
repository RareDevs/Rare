from dataclasses import dataclass
from typing import Optional, List, Dict


@dataclass
class ApiResults:
    game_list: Optional[List] = None
    dlcs: Optional[Dict] = None
    bit32_games: Optional[List] = None
    mac_games: Optional[List] = None
    no_asset_games: Optional[List] = None
    saves: Optional[List] = None

    def __bool__(self):
        return (
            self.game_list is not None
            and self.dlcs is not None
            and self.bit32_games is not None
            and self.mac_games is not None
            and self.no_asset_games is not None
            and self.saves is not None
        )

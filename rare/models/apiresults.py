from dataclasses import dataclass
from typing import Optional, List, Dict

from legendary.models.game import Game, SaveGameFile


@dataclass
class ApiResults:
    games: Optional[List[Game]] = None
    dlcs: Optional[Dict[str, List[Game]]] = None
    bit32_games: Optional[List] = None
    mac_games: Optional[List] = None
    na_games: Optional[List[Game]] = None
    na_dlcs: Optional[Dict[str, List[Game]]] = None
    saves: Optional[List[SaveGameFile]] = None

    def __bool__(self):
        return (
            self.games is not None
            and self.dlcs is not None
            and self.bit32_games is not None
            and self.mac_games is not None
            and self.na_games is not None
            and self.na_dlcs is not None
            and self.saves is not None
        )

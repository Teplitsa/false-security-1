from enum import Enum
from typing import List

from dataclasses import dataclass


class UiCardType(Enum):
    Defence = 0
    Offence = 1
    Accident = 2


@dataclass
class CardPairing:
    other_card: int
    value: int


@dataclass
class UiPlayer:
    id: int
    name: str
    is_admin: bool
    is_online: bool
    on_offence: bool
    on_defence: bool


@dataclass
class UiCard:
    id: int
    name: str
    text: str
    type: UiCardType
    damage: int
    def_against: List[CardPairing]
    off_against: List[CardPairing]
    dealt_by_player: int


# Game references other objects directly, and other objects reference each other by IDs
@dataclass
class UiGame:
    game_name: str
    players: List[UiPlayer]
    self_player: int
    hand: List[UiCard]
    table: List[UiCard]
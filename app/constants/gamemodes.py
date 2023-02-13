from __future__ import annotations

import functools
from enum import IntEnum
from enum import unique
from typing import Any
from typing import Literal
from typing import Union

from app.constants.mods import Mods
from app.utils import escape_enum
from app.utils import pymysql_encode

__all__ = ("GAMEMODE_REPR_LIST", "GameMode")

GAMEMODE_REPR_LIST = (
    "vn!std",
    "vn!taiko",
    "vn!catch",
    "vn!mania",
    "rx!std",
    "rx!taiko",
    "rx!catch",
    "rx!mania",  # unused
    "ap!std",
    "ap!taiko",  # unused
    "ap!catch",  # unused
    "ap!mania",  # unused
)

#TODO: Rework 5 below dicts this to use 1 function maybe 2 instead of this bloat
GAMEMODE_REPR_LIST = (
    "vn!std",
    "vn!taiko",
    "vn!catch",
    "vn!mania",
    "rx!std",
    "rx!taiko",
    "rx!catch",
    "rx!mania",  # unused
    "ap!std",
    "ap!taiko",  # unused
    "ap!catch",  # unused
    "ap!mania",  # unused
)

GULAG_2_INT_DEFAULT = {
    "vn!std": 0,
    "vn!taiko": 1,
    "vn!catch": 2,
    "vn!mania": 3,
    "rx!std": 0,
    "rx!taiko": 1,
    "rx!catch": 2,
    "rx!mania": 3,
    "ap!std": 0,
    "ap!taiko": 1,
    "ap!catch": 2,
    "ap!mania": 3,
}

GULAG_2_INT = {
    "vn!std": 0,
    "vn!taiko": 1,
    "vn!catch": 2,
    "vn!mania": 3,
    "rx!std": 4,
    "rx!taiko": 5,
    "rx!catch": 6,
    "rx!mania": 7,
    "ap!std": 8,
    "ap!taiko": 9,
    "ap!catch": 10,
    "ap!mania": 11,
}

GULAG_2_STR_DEFUALT = {
    "vn!std": "std",
    "vn!taiko": "taiko",
    "vn!catch": "catch",
    "vn!mania": "mania",
    "rx!std": "std",
    "rx!taiko": "taiko",
    "rx!catch": "catch",
    "rx!mania": "mania",
    "ap!std": "std",
    "ap!taiko": "taiko",
    "ap!catch": "catch",
    "ap!mania": "mania",
}

INT_GULAG_2_STR_DEFUALT = {
    0: "std",
    1: "taiko",
    2: "catch",
    3: "mania",
    4: "std",
    5: "taiko",
    6: "catch",
    7: "mania",
    8: "std",
    9: "taiko",
    10: "catch",
    11: "mania",
}

GULAG_INT_2_INT_DEFAULT = {
    0: 0,
    1: 1,
    2: 2,
    3: 3,
    4: 0,
    5: 1,
    6: 2,
    7: 3,
    8: 0,
    9: 1,
    10: 2,
    11: 3,
}

@unique
@pymysql_encode(escape_enum)
class GameMode(IntEnum):
    VANILLA_OSU = 0
    VANILLA_TAIKO = 1
    VANILLA_CATCH = 2
    VANILLA_MANIA = 3

    RELAX_OSU = 4
    RELAX_TAIKO = 5
    RELAX_CATCH = 6
    RELAX_MANIA = 7  # unused

    AUTOPILOT_OSU = 8
    AUTOPILOT_TAIKO = 9  # unused
    AUTOPILOT_CATCH = 10  # unused
    AUTOPILOT_MANIA = 11  # unused

    @classmethod
    def from_params(cls, mode_vn: int, mods: Mods) -> GameMode:
        mode = mode_vn

        if mods & Mods.AUTOPILOT:
            mode += 8
        elif mods & Mods.RELAX:
            mode += 4

        return cls(mode)

    @classmethod
    @functools.cache
    def valid_gamemodes(cls) -> list[GameMode]:
        ret = []
        for mode in cls:
            if mode not in (
                cls.RELAX_MANIA,
                cls.AUTOPILOT_TAIKO,
                cls.AUTOPILOT_CATCH,
                cls.AUTOPILOT_MANIA,
            ):
                ret.append(mode)
        return ret

    @property
    def as_vanilla(self) -> int:
        return self.value % 4

    def __repr__(self) -> str:
        return GAMEMODE_REPR_LIST[self.value]
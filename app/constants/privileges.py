from __future__ import annotations

from enum import IntEnum
from enum import IntFlag
from enum import unique

from app.utils import escape_enum
from app.utils import pymysql_encode

__all__ = ("Privileges", "ClientPrivileges", "ClanPrivileges")


@unique
@pymysql_encode(escape_enum)
class OldPrivileges(IntFlag):
    """Server side user privileges."""

    # privileges intended for all normal players.
    UNRESTRICTED = 1 << 0  # is an unbanned player.
    VERIFIED = 1 << 1  # has logged in to the server in-game.

    # has bypass to low-ceiling anticheat measures (trusted).
    WHITELISTED = 1 << 2

    # donation tiers, receives some extra benefits.
    SUPPORTER = 1 << 4
    PREMIUM = 1 << 5

    # notable users, receives some extra benefits.
    ALUMNI = 1 << 7

    # staff permissions, able to manage server app.state.
    TOURNEY_MANAGER = 1 << 10  # able to manage match state without host.
    NOMINATOR = 1 << 11  # able to manage maps ranked status.
    MODERATOR = 1 << 12  # able to manage users (level 1).
    ADMINISTRATOR = 1 << 13  # able to manage users (level 2).
    DEVELOPER = 1 << 14  # able to manage full server app.state.

    DONATOR = SUPPORTER | PREMIUM
    PERKS = (
        SUPPORTER | PREMIUM | ALUMNI | NOMINATOR | MODERATOR | ADMINISTRATOR | DEVELOPER
    )
    STAFF = MODERATOR | ADMINISTRATOR | DEVELOPER


@unique
@pymysql_encode(escape_enum)
class Privileges(IntFlag):
    UNRESTRICTED = 1 << 0
    VERIFIED = 1 << 1
    FROZEN = 1 << 2

    WHITELISTED_STD_VN = 1 << 3
    WHITELISTED_TAIKO_VN = 1 << 4
    WHITELISTED_CATCH_VN = 1 << 5
    WHITELISTED_MANIA_VN = 1 << 6
    WHITELISTED_STD_RX = 1 << 7
    WHITELISTED_TAIKO_RX = 1 << 8
    WHITELISTED_CATCH_RX = 1 << 9
    WHITELISTED_STD_AP = 1 << 10

    SUPPORTER = 1 << 15
    ALUMNI = 1 << 16
    TOURNAMENT_MANAGER = 1 << 17

    NOMINATOR_STD = 1 << 20
    NOMINATOR_TAIKO = 1 << 21
    NOMINATOR_CATCH = 1 << 22
    NOMINATOR_MANIA = 1 << 23
    QAT_STD = 1 << 24
    QAT_TAIKO = 1 << 25
    QAT_CATCH = 1 << 26
    QAT_MANIA = 1 << 27

    MODERATOR = 1 << 28
    COMMUNITY_MANAGER = 1 << 29
    ADMINISTRATOR = 1 << 30
    HEADADMIN = 1 << 31
    DEVELOPER = 1 << 32
    OWNER = 1 << 33

    NOMINATORS = NOMINATOR_STD | NOMINATOR_CATCH | NOMINATOR_TAIKO | NOMINATOR_MANIA
    QATS = QAT_STD | QAT_CATCH | QAT_TAIKO | QAT_MANIA
    PERKS = (
        SUPPORTER
        | ALUMNI
        | NOMINATORS
        | QATS
        | MODERATOR
        | COMMUNITY_MANAGER
        | ADMINISTRATOR
        | HEADADMIN
        | DEVELOPER
        | OWNER
    )
    STAFF = (
        MODERATOR | COMMUNITY_MANAGER | ADMINISTRATOR | HEADADMIN | DEVELOPER | OWNER
    )

    WHITELISTED = (
        WHITELISTED_STD_VN |
        WHITELISTED_TAIKO_VN |
        WHITELISTED_CATCH_VN |
        WHITELISTED_MANIA_VN |

        WHITELISTED_STD_RX |
        WHITELISTED_TAIKO_RX |
        WHITELISTED_CATCH_RX |

        WHITELISTED_STD_AP
    )



@unique
@pymysql_encode(escape_enum)
class ClientPrivileges(IntFlag):
    """Client side user privileges."""

    PLAYER = 1 << 0
    MODERATOR = 1 << 1
    SUPPORTER = 1 << 2
    OWNER = 1 << 3
    DEVELOPER = 1 << 4
    TOURNAMENT = 1 << 5  # NOTE: not used in communications with osu! client


@unique
@pymysql_encode(escape_enum)
class ClanPrivileges(IntEnum):
    """A class to represent a clan members privs."""

    Member = 1
    Officer = 2
    Owner = 3

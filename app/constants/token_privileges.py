from __future__ import annotations

from enum import IntEnum
from enum import IntFlag
from enum import unique

from app.utils import escape_enum
from app.utils import pymysql_encode

__all__ = "TokenPrivileges"


@unique
@pymysql_encode(escape_enum)
class TokenPrivileges(IntFlag):
    """Token privileges to do certain things on api."""

    # Normal User Stuff
    LOGIN = 1 << 0
    EDIT_SETTINGS = 1 << 1
    POST_CONTENT = 1 << 2  # Sending PMs, posting on articles/maps, etc

    POST_ARTICLES = 1 << 3  # Community Manager, dev+ only

    NOMINATIONS = 1 << 4  # Nominator, dev+ only

    # Admin Stuff
    LOGIN_ADMIN_PANEL = 1 << 10
    EDIT_USERS = 1 << 11
    EDIT_PUNISHMENTS = 1 << 12
    READ_USERS_FULL = 1 << 13

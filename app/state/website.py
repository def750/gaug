__all__ = ("db", "version", "cache")

from typing import TYPE_CHECKING
from typing import Union

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from cmyui.version import Version

version: "Version"

cache = {"bcrypt": {}}

invalid_logins = {}

tokens: dict[int, dict[int]] = {}

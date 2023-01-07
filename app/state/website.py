__all__ = ('db', 'version', 'cache')

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from aiohttp import ClientSession
    from cmyui.mysql import AsyncSQLPool
    from cmyui.version import Version

db: 'AsyncSQLPool'
version: 'Version'

cache = {
    'bcrypt': {}
}
from __future__ import annotations

from typing import TYPE_CHECKING

from . import cache
from . import services
from . import sessions
from . import bot
from . import website

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop

loop: AbstractEventLoop
packets = {"all": {}, "restricted": {}}
shutting_down = False

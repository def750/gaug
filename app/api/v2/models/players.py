from __future__ import annotations

from typing import Optional

from . import BaseModel


# input models


# output models


class Player(BaseModel):
    id: int
    name: str
    safe_name: str

    priv: int
    country: str
    silence_end: int
    donor_end: int
    creation_time: int
    latest_activity: int

    clan_id: int
    clan_priv: int

    preferred_mode: int
    play_style: int

    custom_badge_name: Optional[str]
    custom_badge_icon: Optional[str]

    userpage_content: Optional[str]

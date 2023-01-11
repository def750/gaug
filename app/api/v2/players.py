""" bancho.py's v2 apis for interacting with players """
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from fastapi import status
from fastapi.param_functions import Query

from app.api.v2.common import responses
from app.api.v2.common.responses import Success
from app.api.v2.models.players import Player
from app.repositories import players as players_repo

router = APIRouter()


@router.get("/players")
async def get_players(
    priv: Optional[int] = None,
    country: Optional[str] = None,
    clan_id: Optional[int] = None,
    clan_priv: Optional[int] = None,
    preferred_mode: Optional[int] = None,
    play_style: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> Success[list[Player]]:
    players = await players_repo.fetch_many(
        priv=priv,
        country=country,
        clan_id=clan_id,
        clan_priv=clan_priv,
        preferred_mode=preferred_mode,
        play_style=play_style,
        page=page,
        page_size=page_size,
    )
    total_players = await players_repo.fetch_count(
        priv=priv,
        country=country,
        clan_id=clan_id,
        clan_priv=clan_priv,
        preferred_mode=preferred_mode,
        play_style=play_style,
    )

    response = [Player.from_mapping(rec) for rec in players]

    return responses.success(
        content=response,
        meta={
            "total": total_players,
            "page": page,
            "page_size": page_size,
        },
    )


@router.get("/players/{player_id}")
async def get_player(player_id: int) -> Success[Player]:
    data = await players_repo.fetch_one(id=player_id)
    if data is None:
        return responses.failure(
            message="Player not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    response = Player.from_mapping(data)
    return responses.success(response)

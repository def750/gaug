import datetime as dt
import pprint
from typing import Optional
import app.settings
import app.state.services
import app.state.website
import app.api.v2.utils.authentication as authutils
import Cryptodome.Hash.MD5 as md5

import app.repositories.players


async def save_to_database(
    userid: int,
    token: str,
    client_agent: str,
    ip_address: str,
    issued: int,
    expires: int,
) -> None:
    """Save token to database"""
    print(locals())

    print(type(issued), type(expires))
    if type(issued) is not int or type(expires) is not int:
        raise TypeError(
            "issued and expires must be int timestamps (seconds since epoch)"
        )

    # Validate token
    if not authutils.validate_token(token):
        return None
    else:
        # Hash token with md5
        # token = md5.new(token.encode("utf-8")).hexdigest()
        token = md5.new(token).hexdigest()

    # Save token to database
    await app.state.services.database.execute(
        """
        INSERT INTO tokens (userid, token, issuer_agent, issuer_ip, issue_date, expiration_date)
        VALUES (:userid, :token, :issuer_agent, :issuer_ip, :issue_date, :expiration_date)
        """,
        {
            "userid": userid,
            "token": token,
            "issuer_agent": client_agent,
            "issuer_ip": ip_address,
            "issue_date": int(issued),
            "expiration_date": int(expires),
        },
    )
    return None


async def save_to_cache(
    userid: int,
    token: str,
    expires: int,
) -> None:
    """Save token to cache @ app.state"""
    # Check if user is in cache
    if userid not in app.state.website.tokens:
        app.state.website.tokens[userid] = {}

    # Save token to cache
    app.state.website.tokens[userid][token] = expires
    pprint.pprint(app.state.website.tokens)
    return None


async def delete_token(token: str, userid: Optional[int] = None) -> None:
    # Delete from cache
    if userid is None:
        # Decode token
        userid, _, _ = authutils.decode_token(token)

    if userid in app.state.website.tokens:
        if token in app.state.website.tokens[userid]:
            del app.state.website.tokens[userid][token]

    # Delete from database
    await app.state.services.database.execute(
        """
        DELETE FROM website_tokens
        WHERE userid = :userid AND token = :token
        """,
        {
            "userid": userid,
            "token": md5.new(token.encode("utf-8")).hexdigest(),
        },
    )


async def get_user_from_token(token) -> Optional[dict]:
    # else ~300ms
    userid, _, _ = authutils.decode_token(token)
    return await app.repositories.players.fetch_one(userid)

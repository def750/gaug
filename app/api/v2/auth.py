""" bancho.py's v2 apis for authentication """
from __future__ import annotations

import datetime as dt
import pprint
from fastapi import APIRouter
from fastapi import Header
from fastapi import status
from fastapi import Response
from fastapi.param_functions import Query

from app.api.v2.common import responses
from app.api.v2.models.auth import LoginData
from app.api.v2.models.auth import Token
from app.api.v2.utils import authentication as authutils
from app.constants.token_privileges import TokenPrivileges

import app.settings
import app.state.services
import app.state.website
import app.repositories.players
import app.repositories.auth

router = APIRouter()


# POST: auth/login
@router.post(
    path="/auth/login",
    status_code=status.HTTP_200_OK,
    tags=["auth"],
)
async def login(
    response: Response,
    data: LoginData,
    cf_connecting_ip: str = Header(None),
    user_agent: str = Header(None),
    token_privileges: int = Header(1),
):
    """Issue token for user"""
    if cf_connecting_ip is None:
        return responses.failure(
            message="Could not determine client's IP address.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    else:
        # IP related checks
        user_ip = cf_connecting_ip

    if user_ip in app.state.website.invalid_logins:
        # Check if the user has attempted to login too many times
        if app.state.website.invalid_logins[user_ip][0] >= 3:
            # Max 3 invalid logins, block on 4th
            # Check if the last attempt was less than 5 minutes ago
            if dt.datetime.utcnow() - app.state.website.invalid_logins[user_ip][
                1
            ] <= dt.timedelta(minutes=5):
                return responses.failure(
                    message="Too many invalid login attempts. Wait 5 minutes before trying again.",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                )
            else:
                # Reset invalid logins
                app.state.website.invalid_logins[user_ip] = [0, dt.datetime.utcnow()]

    if user_agent is None:
        return responses.failure(
            message="Could not determine client's user agent.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Validate username and password
    user = await app.repositories.players.fetch_one(
        name=data.username,
        fetch_all_fields=True,
    )
    if not user:
        return responses.failure(
            message="Invalid username or password.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not authutils.validate_password(user["pw_bcrypt"], data.pw_md5):
        # Increment invalid logins
        if user_ip in app.state.website.invalid_logins:
            app.state.website.invalid_logins[user_ip][0] += 1
        else:
            app.state.website.invalid_logins[user_ip] = [1, dt.datetime.utcnow()]

        await app.state.services.database.execute(
            "INSERT INTO website_logins (userid, ip, action) "
            "VALUES (:userid, :ip, :action)",
            {
                "userid": user["id"],
                "ip": user_ip,
                "action": "failed_login",
                # "user_agent": user_agent,
            },
        )

        return responses.failure(
            message="Invalid username or password.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # * Login was successful
    token, expire = await authutils.create_token(
        user["id"],
        user["pw_bcrypt"],
        _w_expire=True,
        token_perms=TokenPrivileges(token_privileges),
    )

    await app.state.services.database.execute(
        "INSERT INTO website_logins (userid, ip, action) "
        "VALUES (:userid, :ip, :action)",
        {
            "userid": user["id"],
            "ip": user_ip,
            "action": "login",
            # "user_agent": user_agent,
        },
    )

    # Put token in cache TODO: Test
    await app.repositories.auth.save_to_cache(token, user["id"], expire)
    await app.repositories.auth.save_to_database(
        user["id"],
        token,
        user_agent,
        user_ip,
        int(dt.datetime.utcnow().timestamp()),
        int(expire),
    )

    response.headers["Content-Type"] = "application/json; charset=utf-8"
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    return Token(token=token, expires=expire)


@router.get(
    path="/auth/check",
)
async def check(response: Response, token: str = Header(None)):
    """Check if token is valid"""
    token_status = await authutils.validate_token(token) if token != None else None

    if token_status != "OK":
        return responses.failure(
            message=token_status,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    return responses.success(content={"valid": True})


if app.settings is True:

    @router.get(
        path="/auth/test",
    )
    async def test(response: Response, token: str = Header(None)):
        """Route for testing"""
        pprint.pprint(app.state.website.tokens)

        return responses.success(content={"valid": True})


@router.get(
    path="/auth/logout",
)
async def logout(response: Response, token: str = Header(None)):
    # Delete token
    await app.repositories.auth.delete_token(token=token)


@router.get(
    path="/auth/@me",
)
async def me(response: Response, token: str = Header(None)):
    if token is None:
        return responses.failure(
            message="No token provided.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    token_status = await authutils.validate_token(token)
    if token_status != "OK":
        return responses.failure(
            message=token_status,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    userid, _, _, _ = authutils.decode_token(token)
    user = await app.state.services.database.fetch_one(
        """
        SELECT id, name, safe_name, priv, preferred_mode
        FROM users
        WHERE id = :userid
        """,
        {"userid": userid},
    )

    return responses.success(content=dict(user))

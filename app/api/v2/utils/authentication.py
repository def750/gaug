from typing import Any, Union, Literal, Optional

import app.settings
import base64
import bcrypt
import secrets
import datetime as dt
import binascii
import app.state
from Cryptodome.Cipher import AES
from app.constants.token_privileges import TokenPrivileges


async def create_token(
    userid: int,
    pw_bcrypt: Optional[str],
    _w_expire: Optional[bool] = False,
    token_perms: TokenPrivileges = 1,
) -> Union[str, tuple[str, int]]:
    """Create token for user
    userid: User ID
    pw_bcrypt: User's password hashed with bcrypt (from DB)
    _w_expire: If True, returns token and expiration timestamp in seconds
    Returns token encoded in base64
    """
    # * Create session token
    今 = int(dt.datetime.utcnow().timestamp())

    # Create token
    token = f"{userid}:{token_perms}:{今}:{secrets.token_hex(16)}:{pw_bcrypt}"

    # Encrypt token with AES
    cipher = AES.new(app.settings.SECRET_KEY.encode(), AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(token.encode("utf-8"))

    if token_perms > 2**10:
        if _w_expire:
            return base64.b64encode(cipher.nonce + tag + ciphertext), 今 + 86400
        else:  # Return token
            return base64.b64encode(cipher.nonce + tag + ciphertext)

    if _w_expire:
        return base64.b64encode(cipher.nonce + tag + ciphertext), 今 + 2592000
    else:  # Return token
        return base64.b64encode(cipher.nonce + tag + ciphertext)


def decode_token(
    token: str,
) -> Union[tuple[int, TokenPrivileges, int, str], None]:
    """Decode token
    token: Token to decode
    Response: Tuple of userid, timestamp and password hash
    """
    # Session token structure:
    # <nonce><tag><ciphertext>
    # First decode base64
    try:
        token = base64.b64decode(token)
        # Get nonce, tag and ciphertext
        nonce, tag, ciphertext = token[:16], token[16:32], token[32:]

        cipher = AES.new(app.settings.SECRET_KEY.encode(), AES.MODE_EAX, nonce)
        token: bytes = cipher.decrypt_and_verify(ciphertext, tag).decode("utf-8")
    except (ValueError, binascii.Error, TypeError, UnicodeDecodeError):
        return None

    # Split token to 4 parts by dot, limit to 4 parts becasuse there might be dots in the password
    userid, tpriv, timestamp, _, pw_bcrypt = token.split(":", 4)

    return (int(userid), TokenPrivileges(int(tpriv)), int(timestamp), pw_bcrypt)

    # return int(userid), int(timestamp), auth_str


async def validate_token(token: str) -> str:
    """Validate token"""
    # Check if token is valid
    try:
        userid, tpriv, timestamp, token = decode_token(token)
    except TypeError:
        return "Invalid token format or token is corrupted"

    # Check if token is expired (timestamp older than 30 days)
    if dt.datetime.utcnow().timestamp() - timestamp > 2592000:
        return "Token expired"

    # Check if password matches with token
    pw_bcrypt = await app.state.services.database.fetch_val(
        "SELECT pw_bcrypt FROM users WHERE id=:userid", {"userid": userid}
    )
    if pw_bcrypt is None:
        return "User not found"

    if pw_bcrypt != token:
        return "Invalid token"

    return "OK"


def validate_password(pw_bcrypt: str, pw_md5: str, w_save: bool = True) -> bool:
    """Validates password.
    w_save: Save password to cache for faster login next time."""
    # Hash password bcrypt
    pwd_bcrypt = pw_bcrypt.encode()
    pw_md5 = pw_md5.encode()

    # Slow on purpose, will chache to speed up
    if pwd_bcrypt in app.state.cache.bcrypt:  # ~0.1ms
        if pw_md5 != app.state.cache.bcrypt[pwd_bcrypt]:
            return False
        else:
            return True
    elif bcrypt.checkpw(pw_md5, pwd_bcrypt):  # ~200-300ms
        # Login successful Save pw_bcrypt to cache
        if w_save == True:
            app.state.cache.bcrypt[pwd_bcrypt] = pw_md5
        return True
    else:
        return False



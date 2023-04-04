# Privilege migration script
# export enum Privileges {
#   // Normal users
#   UNRESTRICTED = 1 << 0,
#   VERIFIED = 1 << 1,
#   FROZEN = 1 << 3, // Read-only mode for the user

#   // Elevated users
#   WHITELISTED = 1 << 5, // has bypass to low-ceiling anticheat measures (trusted).
#   SUPPORTER = 1 << 6, // Has supporter tag
#   ALUMNI = 1 << 7, // Ex-Staff member with big contributions
#   TOURNAMENT_MANAGER = 1 << 8, // Can create tournaments

#   // Staff (Nominators) Access to ranking maps
#   NOMINATOR_STD = 1 << 10,
#   NOMINATOR_CATCH = 1 << 11,
#   NOMINATOR_TAIKO = 1 << 12,
#   NOMINATOR_MANIA = 1 << 13,
#   QAT_STD = 1 << 14,
#   QAT_CATCH = 1 << 15,
#   QAT_TAIKO = 1 << 16,
#   QAT_MANIA = 1 << 17,

#   MODERATOR = 1 << 18, // Access to moderation tools
#   COMMUNITY_MANAGER = 1 << 19, // MOD+ADMIN + Posting articles and news
#   ADMINISTRATOR = 1 << 20, // MOD + ADMIN
#   HEADADMIN = 1 << 21, // MOD+ADMIN + Managing staff
#   DEVELOPER = 1 << 22, // Full access to everything
#   OWNER = 1 << 23, // Allmighty one

#   NOMINATORS = NOMINATOR_STD |
#     NOMINATOR_CATCH |
#     NOMINATOR_TAIKO |
#     NOMINATOR_MANIA,

#   QATS = QAT_STD | QAT_CATCH | QAT_TAIKO | QAT_MANIA,

#   PERKS = SUPPORTER |
#     ALUMNI |
#     NOMINATORS |
#     QATS |
#     MODERATOR |
#     COMMUNITY_MANAGER |
#     ADMINISTRATOR |
#     HEADADMIN |
#     DEVELOPER |
#     OWNER,

#   STAFF = MODERATOR |
#     COMMUNITY_MANAGER |
#     ADMINISTRATOR |
#     HEADADMIN |
#     DEVELOPER |
#     OWNER
# }

import os
import sys


sys.path.insert(0, os.path.abspath(os.pardir))
os.chdir(os.path.abspath(os.pardir))

try:
    import app.settings
except ModuleNotFoundError:
    print("\x1b[;91mMust run from tools/ directory\x1b[m")
    raise


import asyncio
import databases
import aioredis


async def main():
    # Connect to DBs
    db = databases.Database(app.settings.DB_DSN)
    await db.connect()
    redis = await aioredis.from_url(app.settings.REDIS_DSN)

    # Get all users
    users = [
        dict(el)
        for el in await db.fetch_all(
            """
            SELECT u.id, u.priv, u.country, s.pp, s.mode
            FROM stats s
            INNER JOIN users u
            ON s.id = u.id
            WHERE u.priv & 1
            """
        )
    ]

    for u in users:
        # Inset into redis
        await redis.zadd(
            f"bancho:leaderboard:{u['mode']}",
            {str(u["id"]): u["pp"]},
        )

        await redis.zadd(
            f"bancho:leaderboard:{u['mode']}:{u['country']}",
            {str(u["id"]): u["pp"]},
        )

    await db.disconnect()


asyncio.run(main())

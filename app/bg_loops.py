from __future__ import annotations

import asyncio
import time

import app.packets
import app.settings
import app.state
from app.constants.privileges import Privileges
from app.logging import Ansi
from app.logging import log

__all__ = ("initialize_housekeeping_tasks",)

OSU_CLIENT_MIN_PING_INTERVAL = 300000 // 1000  # defined by osu!


async def initialize_housekeeping_tasks() -> None:
    """Create tasks for each housekeeping tasks."""
    log("Initializing housekeeping tasks.", Ansi.LCYAN)

    loop = asyncio.get_running_loop()

    app.state.sessions.housekeeping_tasks.update(
        {
            loop.create_task(task)
            for task in (
                _remove_expired_donation_privileges(interval=30 * 60),
                _update_bot_status(interval=5 * 60),
                _disconnect_ghosts(interval=OSU_CLIENT_MIN_PING_INTERVAL // 3),
                _website(),
            )
        },
    )


async def _remove_expired_donation_privileges(interval: int) -> None:
    """Remove donation privileges from users with expired sessions."""
    while True:
        if app.settings.DEBUG:
            log("Removing expired donation privileges.", Ansi.LMAGENTA)

        expired_donors = await app.state.services.database.fetch_all(
            "SELECT id FROM users "
            "WHERE donor_end <= UNIX_TIMESTAMP() "
            "AND priv & 48",  # 48 = Supporter | Premium
        )

        for expired_donor in expired_donors:
            p = await app.state.sessions.players.from_cache_or_sql(
                id=expired_donor["id"],
            )

            assert p is not None

            # TODO: perhaps make a `revoke_donor` method?
            await p.remove_privs(Privileges.DONATOR)
            p.donor_end = 0
            await app.state.services.database.execute(
                "UPDATE users SET donor_end = 0 WHERE id = :id",
                {"id": p.id},
            )

            if p.online:
                p.enqueue(
                    app.packets.notification("Your supporter status has expired."),
                )

            log(f"{p}'s supporter status has expired.", Ansi.LMAGENTA)

        await asyncio.sleep(interval)


async def _disconnect_ghosts(interval: int) -> None:
    """Actively disconnect users above the
    disconnection time threshold on the osu! server."""
    while True:
        await asyncio.sleep(interval)
        current_time = time.time()

        for p in app.state.sessions.players:
            if current_time - p.last_recv_time > OSU_CLIENT_MIN_PING_INTERVAL:
                log(f"Auto-dced {p}.", Ansi.LMAGENTA)
                p.logout()


async def _update_bot_status(interval: int) -> None:
    """Re roll the bot status, every `interval`."""
    while True:
        await asyncio.sleep(interval)
        app.packets.bot_stats.cache_clear()



#Website imports
import aiohttp
import orjson
from quart import Quart
from quart import render_template
from quart import send_from_directory
from cmyui.logging import Ansi, log
import zenith.zconfig as zconf
from app.state import website as zglob
from hypercorn.asyncio import serve
from hypercorn.config import Config


import datetime as dt
#! Website runner
async def _website() -> None:
    app = Quart(__name__,
                template_folder='/opt/gaug/zenith/templates/',
                root_path='/opt/gaug/zenith/',
                static_folder='/opt/gaug/zenith/static/',
                instance_path='/opt/gaug/zenith/')

    version = "1.3.0"

    # used to secure session data.
    # we recommend using a long randomly generated ascii string.
    app.secret_key = zconf.secret_key
    app.permanent_session_lifetime = dt.timedelta(days=30)
    @app.before_serving
    async def http_conn() -> None:
        zglob.http = aiohttp.ClientSession(json_serialize=orjson.dumps)
        log('ZENITH: Got our Client Session!', Ansi.LGREEN)

    # globals which can be used in template code
    _version = repr(version)
    @app.before_serving
    @app.template_global()
    def appVersion() -> str:
        return _version

    _app_name = zconf.app_name_short
    @app.before_serving
    @app.template_global()
    def appName() -> str:
        return _app_name

    _app_name_l = zconf.app_name_long
    @app.before_serving
    @app.template_global()
    def appNameLong() -> str:
        return _app_name_l

    _captcha_key = zconf.hCaptcha_sitekey
    @app.before_serving
    @app.template_global()
    def captchaKey() -> str:
        return _captcha_key

    _domain = zconf.domain
    @app.before_serving
    @app.template_global()
    def domain() -> str:
        return _domain

    from zenith.blueprints.frontend import frontend
    app.register_blueprint(frontend)
    from zenith.blueprints.api import api
    app.register_blueprint(api, url_prefix="/wapi")
    from zenith.blueprints.admin import admin
    app.register_blueprint(admin, url_prefix="/admin")

    @app.errorhandler(404)
    async def page_not_found(e):
        # NOTE: we set the 404 status explicitly
        return (await render_template(f'errors/404.html'), 404)

    # Custom static data
    @app.route('/cdn/tw-elements/<path:filename>')
    async def custom_static(filename):
        return await send_from_directory('/opt/gulag/zenith/static/js/twelements/', filename)

    #app.run(debug=zconf.debug) # blocking call
    if __name__ == "app.bg_loops":
        await serve(app, Config(), shutdown_trigger=lambda: asyncio.Future())

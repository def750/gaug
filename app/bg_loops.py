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
                _bot()
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
            player = await app.state.sessions.players.from_cache_or_sql(
                id=expired_donor["id"],
            )

            assert player is not None

            # TODO: perhaps make a `revoke_donor` method?
            await player.remove_privs(Privileges.DONATOR)
            player.donor_end = 0
            await app.state.services.database.execute(
                "UPDATE users SET donor_end = 0 WHERE id = :id",
                {"id": player.id},
            )

            if player.online:
                player.enqueue(
                    app.packets.notification("Your supporter status has expired."),
                )

            log(f"{player}'s supporter status has expired.", Ansi.LMAGENTA)

        await asyncio.sleep(interval)


async def _disconnect_ghosts(interval: int) -> None:
    """Actively disconnect users above the
    disconnection time threshold on the osu! server."""
    while True:
        await asyncio.sleep(interval)
        current_time = time.time()

        for player in app.state.sessions.players:
            if current_time - player.last_recv_time > OSU_CLIENT_MIN_PING_INTERVAL:
                log(f"Auto-dced {player}.", Ansi.LMAGENTA)
                player.logout()


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
    app.config['TEMPLATES_AUTO_RELOAD'] = True

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
    from zenith.blueprints.users import users
    app.register_blueprint(users)
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


import discord
import os
from discord.ext import commands
from pathlib import Path
import random
from moai import botconfig
from typing import Literal, Optional
import traceback

async def _bot() -> None:
    """Run the discord bot."""
    intents = discord.Intents.all()
    client = commands.Bot(
        command_prefix=botconfig.PREFIX,
        intents=intents,
        application_id=botconfig.APPLICATION_ID,
    )
    app.state.bot.client = client
    # Enable debug so we don't need to wait for slash commands to propagate


    for dir in os.listdir(f'{botconfig.PATH_TO_FILES}cogs'):
        for file in os.listdir(f'{botconfig.PATH_TO_FILES}cogs/{dir}'):
            if file.endswith('.py') and not file.startswith('_'):
                print(f"[DISCORD BOT] Loading {dir}/{file}...")
                try:
                    await client.load_extension(f'moai.cogs.{dir}.{file[:-3]}')
                except Exception as e:
                    print(f'[DISCORD BOT] Failed to load {dir}/{file}')
                    traceback.print_exc()
                print(f'[DISCORD BOT] Loaded {dir}/{file}')

    @client.event
    async def on_ready() -> None:
        log("[DISCORD BOT] Bot logged in", Ansi.GREEN)
        log(f"Bot name: {client.user.name}")
        log(f"Bot ID: {client.user.id}")
        log(f"Bot Version: {app.state.bot.version}\n")

    @client.command()
    async def rlc(ctx: commands.Context, cog:str='all') -> None:
        """Reloads cog(s)."""

        # Check if user is owner
        if ctx.author.id not in botconfig.OWNERS:
            return await ctx.send("You are not allowed to use this command.", delete_after=10)

        if cog == 'all':
            for dir in os.listdir(f'{botconfig.PATH_TO_FILES}cogs'):
                for file in os.listdir(f'{botconfig.PATH_TO_FILES}cogs/{dir}'):
                    if file.endswith('.py') and not file.startswith('_'):
                        print(f"[DISCORD BOT] Reloading {dir}/{file}...")
                        try:
                            await client.load_extension(f'moai.cogs.{dir}.{file[:-3]}')
                        except Exception as e:
                            print(f'[DISCORD BOT] Failed to reload {dir}/{file}')
                            traceback.print_exc()
                        print(f'[DISCORD BOT] Reloaded {dir}/{file}')

            return await ctx.send("Reloaded all cogs.")

        else:
            # Check if cog exists, and if it's loaded
            for dir in os.listdir(f'{botconfig.PATH_TO_FILES}cogs'):
                for file in os.listdir(f'{botconfig.PATH_TO_FILES}cogs/{dir}'):
                    if file == f'{cog}.py':
                        await client.reload_extension(f'moai.cogs.{dir}.{cog}')
                        return await ctx.send(f"Reloaded {dir}/{cog}.")

        # Cog not found
        return await ctx.send(f"Cog {cog} not found.")

    @client.command()
    async def reloadbot(ctx: commands.Context) -> None:
        """Reloads the bot."""
        # Check if user is owner
        if ctx.author.id not in botconfig.OWNERS:
            return await ctx.send("You are not allowed to use this command.", delete_after=10)

        log("[DISCORD BOT] Reloading whole bot...", Ansi.LYELLOW)
        await ctx.send("Reloading bot, results in console...")
        # Reload the bot
        await client.close()
        await _bot()
        log("[DISCORD BOT] Bot reloaded.", Ansi.LGREEN)

    @client.command()
    @commands.guild_only()
    @commands.is_owner()
    async def sync(
        ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None
    ) -> None:
        if not guilds:
            if spec == "l":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

    await client.start(botconfig.TOKEN)




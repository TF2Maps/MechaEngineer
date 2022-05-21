# Std Lib Imports
import sys
import asyncio
import signal

# 3rd Party Imports
from discord.ext import commands
import discord
from tortoise import Tortoise

# Local Imports
from cogs import *
from utils import load_config, EmbedHelpCommand, setup_logger

config = load_config()
setup_logger(config.log_level)

def main():
    bot = commands.Bot(command_prefix=config.bot_prefix)

    bot.help_command = EmbedHelpCommand()

    # Load Plugins
    bot.add_cog(Misc(bot))
    bot.add_cog(Reporting(bot))
    bot.add_cog(Verification(bot))
    bot.add_cog(Search())
    bot.add_cog(Tags())
    bot.add_cog(MapList())
    bot.add_cog(Servers())
    bot.add_cog(VIP())
    bot.add_cog(ServeMe())

    
    # Setup Asyncio Loop
    bot.loop.add_signal_handler(signal.SIGINT, lambda: bot.loop.stop())
    bot.loop.add_signal_handler(signal.SIGTERM, lambda: bot.loop.stop())

    future = asyncio.ensure_future(start(bot, config.bot_token), loop=bot.loop)
    future.add_done_callback(lambda f: bot.loop.stop())

    try:
        bot.loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        future.remove_done_callback(bot.loop.stop)
        discord.client._cleanup_loop(bot.loop)
    

async def start(bot, token):
    await init_db()

    try:
        await bot.start(token)
    finally:
        if not bot.is_closed:
            await bot.close()

async def init_db():
    await Tortoise.init(
        {
            "connections": {
                "tags": config.databases.tags,
                "starboard": config.databases.starboard,
                "tf2maps_bot": config.databases.tf2maps_bot,
                "tf2maps_site": config.databases.tf2maps_site
            },
            "apps": {
                "tags": {
                    "models": ["models.Tag"],
                    "default_connection": "tags"
                },
                "maplist": {
                    "models": ["models.Maps"],
                    "default_connection": "tf2maps_bot"
                },
                "starboard": {
                    "models": ["models.Starboard"],
                    "default_connection": "starboard"
                },
                "verification": {
                    "models": ["models.Verification"],
                    "default_connection": "tf2maps_bot"
                }
            }
        }
    )
    # await Tortoise.generate_schemas()


async def close():
    await Tortoise.close_connections()


if __name__ == "__main__":
    main()

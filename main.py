# Std Lib Imports
import sys
import asyncio

# 3rd Party Imports
from discord.ext import commands
import discord

# Local Imports
from cogs import *
from emojis import success, warning, error, info
from utils import load_config


def main():
    config = load_config()
    bot = commands.Bot(command_prefix=config.bot_prefix)

    bot.add_cog(Search(bot))
    bot.add_cog(Tags(bot))
    bot.add_cog(MapList(bot))
    bot.add_cog(Servers(bot))
    bot.add_cog(VIP(bot))

    class EmbedHelpCommand(commands.MinimalHelpCommand):
        async def send_pages(self):
            destination = self.get_destination()
            e = discord.Embed(description='')
            for page in self.paginator.pages:
                e.description += page
            await destination.send(embed=e)

    bot.help_command = EmbedHelpCommand()
    bot.run(config.bot_token)

if __name__ == "__main__":
    main()

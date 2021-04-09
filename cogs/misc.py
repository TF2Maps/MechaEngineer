# Std Lib Imports
pass

# 3rd Party Imports
import discord
from discord.ext import commands

# Local Imports
from utils import load_config, cog_error_handler
from emojis import success, warning, error, info, github

global_config = load_config()
config = global_config.cogs.misc

class Misc(commands.Cog):
    cog_command_error = cog_error_handler

    @commands.command(aliases=config.code.aliases, help=config.code.help)
    @commands.has_any_role(*config.code.role_names)
    async def code(self, ctx):
        await ctx.send(f"{github} You can find code my at https://github.com/TF2Maps/TF2M-bot-2021")

    @commands.command(aliases=config.ping.aliases, help=config.ping.help)
    @commands.has_any_role(*config.ping.role_names)
    async def ping(self, ctx):
        await ctx.send(f"Pong")

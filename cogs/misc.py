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

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(activity=discord.Game(name="Team Fortress 2"))

    @commands.command(help=config.code.help)
    @commands.has_any_role(*config.code.role_names)
    async def test(self, ctx):
        pass

    @commands.command(help=config.imp.help)
    @commands.has_any_role(*config.imp.role_names)
    async def imp(self, ctx):
        embed = discord.Embed(
            description=f"{config.imp.description}\n\u200b"
        )
        embed.set_author(name=f"Imp Testing Commands", icon_url=global_config.cogs.search.tf2m_icon)

        for category, text in config.imp.command_list.items():
            embed.add_field(name=f"{category.capitalize()} Commands", value=f"{text}", inline=False)

        embed.set_footer(text=global_config.bot_footer)
        await ctx.send(embed=embed)

    @commands.command(aliases=config.code.aliases, help=config.code.help)
    @commands.has_any_role(*config.code.role_names)
    async def code(self, ctx):
        await ctx.send(f"{github} You can find code my at https://github.com/TF2Maps/TF2M-bot-2021")

    @commands.command(aliases=config.ping.aliases, help=config.ping.help)
    @commands.has_any_role(*config.ping.role_names)
    async def ping(self, ctx):
        await ctx.send(f"Pong")

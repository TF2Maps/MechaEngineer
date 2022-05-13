# Std Lib Imports
from time import strftime
import logging

# 3rd Party Imports
import discord
from discord.ext.commands import Cog, command, has_any_role
from discord.ext import commands

# Local Imports
from utils import load_config, cog_error_handler
from utils.emojis import success, warning, error, info, github
from utils.discord import not_nobot_role

global_config = load_config()
config = global_config.cogs.misc


class Misc(commands.Cog):
    cog_command_error = cog_error_handler

    def __init__(self, bot):
        self.bot = bot

    @Cog.listener(name='on_command')
    async def command_logger(self, ctx):
        logger = logging.getLogger("bot")
        logger.info(f"User {ctx.author.name}({ctx.author.id}) invoked command \"{ctx.command.cog.__class__.__name__}.{ctx.command}\" in #{ctx.channel}")

    @Cog.listener()
    async def on_ready(self):
        month = strftime('%B')
        game_name = "Team Fortress 2"
        if month == "October":
            game_name = "Scream Fortress 2"
        elif month == "February":
            game_name = "Love Fortress 2"
        elif month == "December":
            game_name = "Santa Fortress 2"

        await self.bot.change_presence(activity=discord.Game(name=f"{game_name} | !help"))

    @command(help=config.code.help)
    @has_any_role(*config.code.role_names)
    @not_nobot_role()
    async def test(self, ctx):
        pass

    @discord.slash_command(description="See map test commands.")
    async def imp(self, ctx):
        embed = discord.Embed(
            description=f"{config.imp.description}"
        )
        embed.set_author(name=f"Imp Testing Commands", icon_url=global_config.icons.tf2m_icon)

        for category, text in config.imp.command_list.items():
            embed.add_field(name=f"{category.capitalize()} Commands", value=f"{text}", inline=False)

        embed.set_footer(text=global_config.bot_footer)
        await ctx.respond(embed=embed)

    @discord.slash_command(description="See my code.")
    async def code(self, ctx):
        await ctx.respond(f"{github} You can find my code at https://github.com/TF2Maps/TF2M-bot-2021")

    @discord.slash_command(description="Sends the bot's latency.")
    async def ping(self, ctx):
        await ctx.respond(f"Pong! Latency is {bot.latency}")

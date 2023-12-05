# Std Lib Imports
from time import strftime
import logging

# 3rd Party Imports
import discord
from discord.ext.commands import Cog, slash_command

# Local Imports
from utils import load_config, cog_error_handler
from utils.emojis import github
from utils.discord import not_nobot_role_slash, roles_required

global_config = load_config()
config = global_config.cogs.misc


class Misc(Cog):
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

        await self.bot.change_presence(activity=discord.Game(name=f"{game_name}"))

        #server_channel = self.bot.get_channel(1127280330710192281)
        #await server_channel.send('** **')

    @slash_command(
        name="imp", 
        description=config.imp.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.imp.role_names),
            not_nobot_role_slash()
        ]
    )
    async def imp(self, ctx):
        embed = discord.Embed(
            description=f"{config.imp.description}"
        )
        embed.set_author(name=f"Imp Testing Commands", icon_url=global_config.icons.tf2m_icon)

        for category, text in config.imp.command_list.items():
            embed.add_field(name=f"{category.capitalize()} Commands", value=f"{text}", inline=False)

        embed.set_footer(text=global_config.bot_footer)
        await ctx.respond(embed=embed)

    @slash_command(
        name="code", 
        description=config.code.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.code.role_names),
            not_nobot_role_slash()
        ]
    )
    async def code(self, ctx):
        await ctx.respond(f"{github} You can find my code at https://github.com/TF2Maps/MechaEngineer")

    @slash_command(
        name="ping", 
        description=config.ping.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.ping.role_names),
            not_nobot_role_slash()
        ]
    )
    async def ping(self, ctx):
        await ctx.respond(f"Pong")

    @slash_command(
        name="rules", 
        description=config.rules.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.rules.role_names),
            not_nobot_role_slash()
        ]
    )
    async def rules(self, ctx):
        embed = discord.Embed(
            description=f"{config.rules.description}"
        )

        embed.add_field(name=f"", value=f"{config.rules.the_rules}", inline=False)

        embed.set_footer(text=global_config.bot_footer)
        await ctx.respond(embed=embed, ephemeral=True)

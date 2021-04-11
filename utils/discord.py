# Std Lib Imports
import traceback

# 3rd Party Imports
import discord
from discord.ext import commands

# Local Imports
from .emojis import error


class EmbedHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        embed = discord.Embed(description='')
        embed.set_author(name=f"Help", icon_url=global_config.icons.info_icon)
        embed.set_footer(text=global_config.bot_footer)

        for page in self.paginator.pages:
            embed.description += page
        embed.description = embed.description.replace("\n__**\u200bNo Category**__\nhelp", "")
        embed.description = embed.description.replace("\n__", "\n\n__")

        await destination.send(embed=embed)


async def cog_error_handler(self, ctx, error_message):
    if isinstance(error_message, commands.BadArgument):
        await ctx.send(f"{error} {error_message}")
    elif isinstance(error_message, commands.TooManyArguments):
        await ctx.send(f'{error} Too many arguments.')
        await ctx.send_help(ctx.command)
    elif isinstance(error_message, commands.MissingRequiredArgument):
        await ctx.send(f"{error} Missing required arugments")
        await ctx.send_help(ctx.command)
    elif isinstance(error_message, commands.MissingAnyRole):
        await ctx.send(f"{error} {error_message}")
    else:
        tb = traceback.format_exception(None, error_message.original, error_message.original.__traceback__)
        await ctx.send(f"{error} <@65497519504764928> Unhandled Exception:\n ```\n{''.join(tb)}```")

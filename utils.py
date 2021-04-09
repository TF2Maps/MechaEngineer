import traceback

import discord
from discord.ext import commands
import yaml
from dotted_dict import DottedDict

from emojis import error


def load_config():
    with open("config.yaml") as file:
        config = yaml.load(file)
    return DottedDict(config)


class EmbedHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        embed = discord.Embed(description='')
        embed.set_author(name=f"Help", icon_url="https://cdn.discordapp.com/emojis/829026378078224435.png?v=1")
        embed.set_footer(text="TF2M Bot • v2.0 ᴮᴱᵀᴬ")

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
    else:
        tb = traceback.format_exception(None, error_message.original, error_message.original.__traceback__)
        await ctx.send(f"{error} Unknown error: `{error_message.__class__.__name__}`\n\n<@65497519504764928> ||```\n{''.join(tb)}```||")

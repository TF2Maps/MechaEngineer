import traceback
from copy import copy
from logging import Formatter
import logging
import os
import sys

import discord
from discord.ext import commands
import yaml
from dotted_dict import DottedDict

from emojis import error

def load_config():
    with open("config.yaml") as file:
        config = yaml.load(file)
    return DottedDict(config)

global_config = load_config()

class EmbedHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        embed = discord.Embed(description='')
        embed.set_author(name=f"Help", icon_url="https://cdn.discordapp.com/emojis/829026378078224435.png?v=1")
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
    else:
        tb = traceback.format_exception(None, error_message.original, error_message.original.__traceback__)
        await ctx.send(f"{error} Unknown error: `{error_message.__class__.__name__}`\n\n<@65497519504764928> ||```\n{''.join(tb)}```||")

def setup_logger(level):
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = ColoredFormatter(
        "%(levelname)s \u001b[1;30m%(name)s.%(funcName)s:%(lineno)s \u001b[0m'%(message)s'"
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)

    log = logging.getLogger('')
    log.setLevel(level)
    log.addHandler(console_handler)

class ColoredFormatter(Formatter):
    def __init__(self, patern):
        Formatter.__init__(self, patern)

    def format(self, record):
        MAPPING = {
            'DEBUG': 36,
            'INFO': 32,
            'WARNING': 33,
            'ERROR': 31,
            'CRITICAL': 41,
        }

        PREFIX = '\033[1;'
        SUFFIX = '\033[0m'

        colored_record = copy(record)
        levelname = colored_record.levelname
        seq = MAPPING.get(levelname, 37)

        colored_levelname = (f'{PREFIX}{seq}m{levelname}{SUFFIX}')
        colored_record.levelname = colored_levelname

        return Formatter.format(self, colored_record)
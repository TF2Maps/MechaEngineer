# Std Lib Imports
import traceback

# 3rd Party Imports
import discord
from discord.ext import commands

# Local Imports
from .config import load_config
from .emojis import error

global_config = load_config()

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
        await ctx.send(f"{error} Missing required arguments")
        await ctx.send_help(ctx.command)
    elif isinstance(error_message, commands.MissingAnyRole):
        await ctx.respond(f"{error} {error_message}")
    elif isinstance(error_message, discord.errors.DiscordServerError):
        await ctx.send(f"{error} Discord API returned a fatal error. Try command again later")
    elif isinstance(error_message, discord.ext.commands.errors.CheckFailure):
        await ctx.send(f"{error} You do not meet the critera for using this command.")
    elif isinstance(error_message, discord.errors.CheckFailure):
        await ctx.respond(f"{error} You do not meet the critera for using this command.")
    else:
        tb = traceback.format_exception(None, error_message.original, error_message.original.__traceback__)
        await ctx.send(f"{error} <@65497519504764928> Unhandled Exception:\n ```\n{''.join(tb)}```")

def not_nobot_role():
    """
    TODO: DEPRECATED
    """
    def predicate(ctx):
        for role in ctx.author.roles:
            if role.name == "No Bot":
                return False
        else:
            return True
    return commands.check(predicate)


def not_nobot_role_slash():
    def wrappedf(ctx):
        user_roles = [r.name.lower() for r in ctx.author.roles]

        if "no bot" in user_roles:
            raise discord.errors.CheckFailure
        else:
            return True
    return wrappedf


def roles_required(role_names):
    def wrapped(ctx):
        user_roles = [r.name.lower() for r in ctx.author.roles]

        if "no bot" in user_roles:
            raise discord.errors.CheckFailure

        for role in role_names:
            if role.lower() in user_roles:
                return True
        else: 
            raise discord.ext.commands.MissingAnyRole(role_names)
    return wrapped    
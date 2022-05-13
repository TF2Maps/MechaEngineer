# Std Lib Imports
import re

# 3rd Party Imports
import discord
from discord.ext.commands import Cog, command
from discord.ext import commands

# Local Imports
from utils import load_config, cog_error_handler
from utils.emojis import success, warning, error, info, loading

global_config = load_config()
config = global_config.cogs.modmail


class ModMail(Cog):
    cog_command_error = cog_error_handler

    def __init__(self, bot):
        self.bot = bot
        self.messages_waiting = []

    @Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        success_emoji_id = int(re.search("(\d+)>$", success).groups()[0])
        error_emoji_id = int(re.search("(\d+)>$", error).groups()[0])

        if reaction.user_id == global_config.bot_userid:
            return

        if reaction.emoji.id == success_emoji_id:
            for message in self.messages_waiting:
                if message.id == reaction.message_id:
                    embed = message.embeds[0]
                    self.messages_waiting.remove(message)

                    channel = self.bot.get_channel(config.mod_channel_id)
                    await channel.send(embed=embed)
                    await message.edit(content=f"{success} This message has been sent to the moderators.")

        elif reaction.emoji.id == error_emoji_id:
            for message in self.messages_waiting:
                if message.id == reaction.message_id:
                    embed = message.embeds[0]
                    self.messages_waiting.remove(message)

                await message.edit(content=f"{success} This message never happened.", embed=None)

    @command(aliases=config.amm.aliases, help=config.amm.help)
    @commands.dm_only()
    async def amm(self, ctx, *, message):
        embed = self.get_modmessage_embed(ctx, message, include_author=False)
        message = await ctx.author.send(
            (
                f"{success} = Sends message.\n"
                f"{error} = Cancel message.\n\n"
                "Here is a preview of what staff will see:"
            ),
            embed=embed
        )
        await message.add_reaction(success)
        await message.add_reaction(error)
        self.messages_waiting.append(message)

    @command(aliases=config.mm.aliases, help=config.mm.help)
    @commands.dm_only()
    async def mm(self, ctx, *, message):
        embed = self.get_modmessage_embed(ctx, message, include_author=True)
        message = await ctx.author.send(
            (
                f"{success} = Sends message.\n"
                f"{error} = Cancel message.\n\n"
                "Here is a preview of what staff will see:"
            ),
            embed=embed
        )
        await message.add_reaction(success)
        await message.add_reaction(error)
        self.messages_waiting.append(message)

    @staticmethod
    def get_modmessage_embed(ctx, message, include_author=False):
        embed = discord.Embed(color=0xff9933)

        if include_author:
            embed.set_author(name=f"{ctx.author.name} {ctx.author.id}", icon_url=ctx.author.avatar_url)
        else:
            embed.set_author(name="Anonymous", icon_url=global_config.icons.warning_icon)

        embed.set_footer(text=global_config.bot_footer)

        embed.add_field(name="Message:", value=message, inline=False)

        attachments = ""
        for attachment in ctx.message.attachments:
            attachments += f"{attachment.url}\n"
            embed.description = attachment.url
        if attachments:
            embed.add_field(name="Attachments:", value=attachments, inline=False)

        return embed

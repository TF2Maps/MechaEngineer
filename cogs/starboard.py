# Std Lib Imports
pass

# 3rd Party Imports
import discord
from discord.ext import commands
import valve.source.a2s
from tortoise.functions import Avg, Count, Sum
from tortoise import Tortoise

# Local Imports
from models import Starboard as sb

from utils import load_config, cog_error_handler, get_srcds_server_info
from emojis import success, warning, error, info, loading

global_config = load_config()
config = global_config.cogs.servers


class Starboard(commands.Cog):
    cog_command_error = cog_error_handler

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        valid_reactions = [
            "<:rateLike:348604264819720192>",
            "<:rateAgree:348604264622456832>",
            "<:frogchamp:713121354148478986>",
            "<:rateThanks:348604264681046017>",
            "<:rateFunny:348604264538570753>",
            "<:rateFriendly:348604264739897344>"
        ]
        formatted_reaction = f"<:{reaction.emoji.name}:{reaction.emoji.id}>"

        if reaction.me:
            return
        if not formatted_reaction in valid_reactions:
            return
        if reaction.message.author.id == user.id:
            return

        await sb.create(
            message_id=reaction.message.id,
            message_author_id=reaction.message.author.id,
            reaction_author_id=user.id,
            reaction_emoji=formatted_reaction
        )

    @commands.command()
    async def stars(self, ctx):
        records = await (
            sb.filter(message_author_id=ctx.author.id)
            .all()
            .annotate(emoji_count=Count("reaction_emoji"))
            .group_by("reaction_emoji")
            .order_by("-emoji_count")
            .values_list("reaction_emoji", "emoji_count")
        )

        output = "Heres the stars you've recieved:\n\n"
        for emoji, count in records:
            output += f"{emoji} {count}\n"

        embed = discord.Embed(
            description=output
        )
        embed.set_author(name="Starboard", icon_url="https://cdn.discordapp.com/attachments/655897074172166171/830531144704851998/star.png")
        embed.set_footer(text=global_config.bot_footer)

        await ctx.send(embed=embed)
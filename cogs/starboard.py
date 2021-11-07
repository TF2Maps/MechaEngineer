# Std Lib Imports
pass

# 3rd Party Imports
import discord
from discord.ext.commands import Cog, command, has_any_role
import valve.source.a2s
from tortoise.functions import Avg, Count, Sum
from tortoise import Tortoise

# Local Imports
from models import Starboard as sb

from utils import load_config, cog_error_handler
from utils.emojis import success, warning, error, info, loading

global_config = load_config()
config = global_config.cogs.starboard


class Starboard(Cog):
    cog_command_error = cog_error_handler

    @Cog.listener()
    async def on_reaction_add(self, reaction, user):
        formatted_reaction = f"<:{reaction.emoji.name}:{reaction.emoji.id}>"

        if reaction.me:
            return
        if not formatted_reaction in config.valid_emojis:
            return
        if reaction.message.author.id == user.id:
            return

        await sb.create(
            message_id=reaction.message.id,
            message_author_id=reaction.message.author.id,
            reaction_author_id=user.id,
            reaction_emoji=formatted_reaction
        )

    @command()
    async def stars(self, ctx):
        records = await (
            sb.filter(message_author_id=ctx.author.id)
            .all()
            .annotate(emoji_count=Count("reaction_emoji"))
            .group_by("reaction_emoji")
<<<<<<< HEAD
#            .order_by("-emoji_count")
=======
            .order_by("-emoji_count")
>>>>>>> 0af49079da6c7edef51ab4e65fe47928bde3a227
            .values_list("reaction_emoji", "emoji_count")
        )

        output = "Heres the stars you've recieved:\n\n"
        for emoji, count in records:
            output += f"{emoji} {count}\n"

        embed = discord.Embed(
            description=output
        )
        embed.set_author(name="Starboard", icon_url=global_config.icons.star_icon)
        embed.set_footer(text=global_config.bot_footer)

        await ctx.send(embed=embed)
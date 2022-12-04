# Std Lib Imports
pass

# 3rd Party Imports
import discord
from discord.ext.commands import Cog, Cooldown, slash_command
from discord.commands import SlashCommandGroup
from tabulate import tabulate
from tortoise.expressions import Q

# Local Imports
from models.Tag import Tag
from utils import load_config, cog_error_handler
from utils.emojis import success, warning, error, info
from utils.discord import not_nobot_role_slash, roles_required

global_config = load_config()
config = global_config.cogs.tags


class Tags(Cog):

    cog_command_error = cog_error_handler
    tag = SlashCommandGroup("tag", "Commands for our tag system.", guild_ids=global_config.bot_guild_ids)

    @Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        key = message.content.lower()
        tag = await Tag.filter(key=key).first()
        if tag:
            await message.channel.send(tag.value)

    @tag.command(
        name="create", 
        description=config.create.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.create.role_names),
            not_nobot_role_slash()
        ]
    )
    async def create(self, ctx, key, *, value):
        tag, created = await Tag.get_or_create(
            key=key.lower(),
            value=value,
            author=ctx.author.name
        )

        if created:
            await ctx.respond(f"{success} Created tag `{key}`!")
        else:
            await ctx.respond(f"{error} Tag already exists")
    
    @tag.command(
        name="remove", 
        description=config.remove.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.remove.role_names),
            not_nobot_role_slash()
        ]
    )
    async def remove(self, ctx, key):
        tag = await Tag.get_or_none(key=key)

        if tag:
            await tag.delete()
            await ctx.respond(f"{success} Deleted tag `{key}`!")
        else:
            await ctx.respond(f"{error} Tag `{key}` not found.")

    @tag.command(
        name="list", 
        description=config.list.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.list.role_names),
            not_nobot_role_slash()
        ]
    )
    async def list(self, ctx, *, search):
        tags = await Tag.filter(
            Q(key__icontains=search) | Q(author__icontains=search)
        ).all()

        rows = []
        for tag in tags:
            rows.append([tag.key, tag.value, tag.author])

        table = tabulate(rows, headers=["Key", "Value", "Author"], tablefmt="simple")
        await ctx.respond(f"```diff\n{table}\n```")

    @tag.command(
        name="count", 
        description=config.count.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.count.role_names),
            not_nobot_role_slash()
        ]
    )
    async def count(self, ctx):
        count = await Tag.all().count()
        await ctx.respond(f"{info} There are `{count}` tags.")

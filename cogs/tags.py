# Std Lib Imports
pass

# 3rd Party Imports
import discord
from discord.ext.commands import Cog, command, has_any_role, group
from tabulate import tabulate
from tortoise.expressions import Q

# Local Imports
from models.Tag import Tag
from utils import load_config, cog_error_handler
from utils.emojis import success, warning, error, info
from utils.discord import not_nobot_role

global_config = load_config()
config = global_config.cogs.tags


class Tags(Cog):

    cog_command_error = cog_error_handler

    @Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        key = message.content.lower()
        tag = await Tag.filter(key=key).first()
        if tag:
            await message.channel.send(tag.value)

    @group()
    @has_any_role(*config.create.role_names)
    @not_nobot_role()
    async def tag(self, ctx):
        pass

    @tag.command(aliases=config.create.aliases, help=config.create.help)
    @has_any_role(*config.create.role_names)
    @not_nobot_role()
    async def create(self, ctx, key, *, value):
        tag, created = await Tag.get_or_create(
            key=key.lower(),
            value=value,
            author=ctx.author.name
        )

        if created:
            await ctx.send(f"{success} Created tag `{key}`!")
        else:
            await ctx.send(f"{error} Tag already exists")

    @tag.command(aliases=config.remove.aliases, help=config.remove.help)
    @has_any_role(*config.remove.role_names)
    @not_nobot_role()
    async def remove(self, ctx, key):
        tag = await Tag.get_or_none(key=key)

        if tag:
            await tag.delete()
            await ctx.send(f"{success} Deleted tag `{key}`!")
        else:
            await ctx.send(f"{error} Tag `{key}` not found.")

    @tag.command(aliases=config.list.aliases, help=config.list.help)
    @has_any_role(*config.list.role_names)
    @not_nobot_role()
    async def list(self, ctx, *, search):
        tags = await Tag.filter(
            Q(key__icontains=search) | Q(author__icontains=search)
        ).all()

        rows = []
        for tag in tags:
            rows.append([tag.key, tag.value, tag.author])

        table = tabulate(rows, headers=["Key", "Value", "Author"], tablefmt="simple")
        await ctx.send(f"```diff\n{table}\n```")

    @tag.command(aliases=config.count.aliases, help=config.count.help)
    @has_any_role(*config.count.role_names)
    @not_nobot_role()
    async def count(self, ctx):
        count = await Tag.all().count()
        await ctx.send(f"{info} There are `{count}` tags.")

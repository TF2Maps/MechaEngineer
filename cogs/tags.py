# Std Lib Imports
pass

# 3rd Party Imports
import discord
from discord.ext import commands
from tabulate import tabulate
from tortoise.query_utils import Q

# Local Imports
from models.Tag import Tag
from utils import load_config
from emojis import success, warning, error, info

global_config = load_config()
config = global_config.cogs.tags


class Tags(commands.Cog):

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        key = message.content.lower()
        tag = await Tag.filter(key=key).first()
        if tag:
            await message.channel.send(tag.value)

    @commands.group()
    async def tag(self, ctx):
        pass

    @tag.command(aliases=config.create.aliases, help=config.create.help)
    @commands.has_any_role(*config.create.role_names)
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
    @commands.has_any_role(*config.remove.role_names)
    async def remove(self, ctx, key):
        tag = await Tag.get_or_none(key=key)

        if tag:
            await tag.delete()
            await ctx.send(f"{success} Deleted tag `{key}`!")
        else:
            await ctx.send(f"{error} Tag `{key}` not found.")

    @tag.command(aliases=config.list.aliases, help=config.list.help)
    @commands.has_any_role(*config.list.role_names)
    async def list(self, ctx, *, search):
        tags = await Tag.filter(
            Q(key__icontains=search) | Q(author__icontains=search)
        ).all()

        rows = []
        for tag in tags:
            rows.append([tag.key, tag.value, tag.author])

        table = tabulate(rows, headers=["Key", "Value", "Author"], tablefmt="simple")
        await ctx.send(f"```diff\n{table}\n```")

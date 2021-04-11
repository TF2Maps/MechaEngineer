# Std Lib Imports
import re

# 3rd Party Imports
import discord
from discord.ext.commands import Cog, command, has_any_role
from bs4 import BeautifulSoup
import httpx
import databases

# Local Imports
from utils import load_config, cog_error_handler
from utils.search import search_with_bing, search_downloads

global_config = load_config()
config = global_config.cogs.search


class Search(Cog):
    cog_command_error = cog_error_handler

    @command(aliases=config.vdc.aliases, help=config.vdc.help)
    @has_any_role(*config.vdc.role_names)
    async def vdc(self, ctx, *, term):
        await ctx.trigger_typing()
        site = "developer.valvesoftware.com/wiki"
        links = await search_with_bing(site, term)
        embed = self.get_search_embed(links, term, "Valve Developer Wiki", global_config.icons.vdc_icon, remove_prefix=f"https://{site}/")
        await ctx.send(embed=embed)

    @command(aliases=config.tf2m.aliases, help=config.tf2m.help)
    @has_any_role(*config.tf2m.role_names)
    async def tf2m(self, ctx, *, term):
        await ctx.trigger_typing()
        site = "tf2maps.net"
        links = await search_with_bing(
            site,
            term,
            exclude=[
                "feedback.tf2maps.net",
                "demos.tf2maps.net",
                "bot.tf2maps.net",
            ]
        )
        embed = self.get_search_embed(links, term, "TF2 Maps", global_config.icons.vdc_icon, remove_prefix=f"https://{site}/")
        await ctx.send(embed=embed)

    @command(aliases=config.dl.aliases, help=config.dl.help)
    @has_any_role(*config.dl.role_names)
    async def dl(self, ctx, resource_name):
        site = "tf2maps.net"
        links = await search_downloads(resource_name)
        embed = self.get_search_embed(links, resource_name, "TF2 Maps Downloads", global_config.icons.vdc_icon, remove_prefix=f"https://{site}/downloads/")
        await ctx.send(embed=embed)

    @staticmethod
    def get_search_embed(links, term, title, icon, remove_prefix=""):
        output = f"Showing **{len(links)}** results for `{term}`\n"
        for link in links:
            link_name = link.replace(remove_prefix, "")
            link_name = re.sub("/$", "", link_name)

            if not link_name:
                continue
            output += f"\n• [{link_name}]({link})"

        embed = discord.Embed(
            description=output,
        )
        embed.set_author(name=f"{title} Search", icon_url=icon)
        embed.set_footer(text=global_config.bot_footer)

        return embed
# Std Lib Imports
import re

# 3rd Party Imports
import discord
from discord.ext.commands import Cog, command, has_any_role
from bs4 import BeautifulSoup
import httpx
import databases

#Slash Command Imports
from discord.commands import (
    slash_command,
    Option,
    message_command,
    user_command
)

# Local Imports
from utils import load_config, cog_error_handler
from utils.search import search_with_bing, search_downloads
from utils.emojis import success, warning, error, info, loading
from utils.discord import not_nobot_role

global_config = load_config()
config = global_config.cogs.search


class Search(Cog):
    cog_command_error = cog_error_handler

    @discord.slash_command(description="Search the VDC.")
    async def vdc(self, ctx, *, term: discord.Option(str)):
        await ctx.trigger_typing()
        site = "developer.valvesoftware.com/wiki"
        links = await search_with_bing(site, term)
        embed = self.get_search_embed(links[:10], term, "Valve Developer Wiki", global_config.icons.vdc_icon, remove_prefix=f"https://{site}/")
        try:
            await ctx.respond(embed=embed)
        except discord.errors.HTTPException:
            await ctx.respond(f"{error} Query returned too many results to display. Try a more specific query")

    @discord.slash_command(description="Search the TF2maps.net forums.")
    async def tf2m(self, ctx, *, term: discord.Option(str)):
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
        embed = self.get_search_embed(links[:10], term, "TF2 Maps", global_config.icons.tf2m_icon, remove_prefix=f"https://{site}/")
        try:
            await ctx.respond(embed=embed)
        except discord.errors.HTTPException:
            await ctx.respond(f"{error} Query returned too many results to display. Try a more specific query")

    @discord.slash_command(description="Search the TF2maps.net downloads.")
    async def dl(self, ctx, resource_name: discord.Option(str)):
        site = "tf2maps.net"
        links = await search_downloads(resource_name)
        embed = self.get_search_embed(links[:10], resource_name, "TF2 Maps Downloads", global_config.icons.tf2m_icon, remove_prefix=f"https://{site}/downloads/")
        try:
            await ctx.respond(embed=embed)
        except discord.errors.HTTPException:
            await ctx.respond(f"{error} Query returned too many results to display. Try a more specific query")

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
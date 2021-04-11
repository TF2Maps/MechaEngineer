# Std Lib Imports
import re

# 3rd Party Imports
import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import httpx
import databases

# Local Imports
from utils import load_config, cog_error_handler

global_config = load_config()
config = global_config.cogs.search


class Search(commands.Cog):
    cog_command_error = cog_error_handler

    @commands.command(aliases=config.vdc.aliases, help=config.vdc.help)
    @commands.has_any_role(*config.vdc.role_names)
    async def vdc(self, ctx, *, term):
        await ctx.trigger_typing()
        site = "developer.valvesoftware.com/wiki"
        links = await self.search_with_bing(site, term)
        embed = self.get_search_embed(links, term, "Valve Developer Wiki", global_config.icons.vdc_icon, remove_prefix=f"https://{site}/")
        await ctx.send(embed=embed)

    @commands.command(aliases=config.tf2m.aliases, help=config.tf2m.help)
    @commands.has_any_role(*config.tf2m.role_names)
    async def tf2m(self, ctx, *, term):
        await ctx.trigger_typing()
        site = "tf2maps.net"
        links = await self.search_with_bing(
            site,
            term,
            exclude=[
                "feedback.tf2maps.net",
                "demos.tf2maps.net",
                "bot.tf2maps.net",
                # "tf2maps.net/downloads",
                # "tf2maps.net/threads"
            ]
        )
        embed = self.get_search_embed(links, term, "TF2 Maps", global_config.icons.vdc_icon, remove_prefix=f"https://{site}/")
        await ctx.send(embed=embed)

    @commands.command(aliases=config.dl.aliases, help=config.dl.help)
    @commands.has_any_role(*config.dl.role_names)
    async def dl(self, ctx, resource_name):
        site = "tf2maps.net"
        links = await self.search_downloads(resource_name)
        embed = self.get_search_embed(links, resource_name, "TF2 Maps Downloads", global_config.icons.vdc_icon, remove_prefix=f"https://{site}/downloads/")
        await ctx.send(embed=embed)

    @staticmethod
    async def search_downloads(resource_name, discord_user_id=None):
        database = databases.Database(global_config.databases.tf2maps_site)
        await database.connect()

        results = []
        if discord_user_id:
            query = "SELECT user_id FROM xf_user_field_value WHERE field_id = :field_id AND field_value = :field_value"
            values = {"field_id": "discord_user_id", "field_value": discord_user_id}
            result = await database.fetch_one(query=query, values=values)
            forum_user_id = result[0]
            query = 'SELECT title,resource_id from xf_resource where user_id=:field_user_id AND title LIKE :field_title'
            values = {"field_user_id": forum_user_id, "field_title": f"%{resource_name}%"}
            results = await database.fetch_all(query=query, values=values)

        else:
            query = 'SELECT title,resource_id from xf_resource where title LIKE :field_title ORDER BY resource_id DESC'
            values = {"field_title": f"%{resource_name}%"}
            results = await database.fetch_all(query=query, values=values)

        links = []
        for name, map_id in results:
            name = re.sub("[^A-z0-9_]", "-", name)
            name = re.sub("-+$", "", name)
            name = re.sub("-{2,}", "-", name)
            name = name.lower()

            links.append(f"https://tf2maps.net/downloads/{name}.{map_id}/")

        return links

    @staticmethod
    async def search_with_bing(site, term, exclude=[]):
        plus_term = "%20".join(term.split(" "))
        exclude_sites = "%20".join([f"-site%3A{site}" for site in exclude])
        search_query = f"https://www.bing.com/search?q=site%3A{site}%20{exclude_sites}%20{plus_term}"

        async with httpx.AsyncClient() as client:
            response = await client.get(search_query)

        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.select("ol#b_results > li.b_algo > h2 > a")

        return [link['href'] for link in links]

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
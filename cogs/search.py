# Std Lib Imports
pass

# 3rd Party Imports
import discord
from discord.ext.commands import Cog, slash_command
from discord.commands import SlashCommandGroup

# Local Imports
from utils import load_config, cog_error_handler
from utils.search import search_with_bing, search_downloads
from utils.emojis import error
from utils.discord import not_nobot_role_slash, roles_required


global_config = load_config()
config = global_config.cogs.search


class Search(Cog):
    cog_command_error = cog_error_handler

    search = SlashCommandGroup("search", guild_ids=global_config.bot_guild_ids)

    @search.command(
        name="vdc", 
        description=config.vdc.help, 
        checks=[
            roles_required(config.vdc.role_names),
            not_nobot_role_slash()
        ]
    )
    async def vdc(self, ctx, *, term):
        await ctx.defer()
        site = "developer.valvesoftware.com/wiki"
        links = await search_with_bing(site, term)
        embed = self.get_search_embed(links[:10], term, "Valve Developer Wiki", global_config.icons.vdc_icon, remove_prefix=f"https://{site}/")
        try:
            await ctx.respond(embed=embed)
        except discord.errors.HTTPException:
            await ctx.respond(f"{error} Query returned too many results to display. Try a more specific query")

    @search.command(
        name="tf2maps", 
        description=config.tf2maps.help, 
        checks=[
            roles_required(config.tf2maps.role_names),
            not_nobot_role_slash()
        ]
    )
    async def tf2maps(self, ctx, *, term):
        await ctx.defer()
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

    @search.command(
        name="downloads", 
        description=config.downloads.help, 
        checks=[
            roles_required(config.downloads.role_names),
            not_nobot_role_slash()
        ]
    )
    async def downloads(self, ctx, resource_name):
        await ctx.defer()
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
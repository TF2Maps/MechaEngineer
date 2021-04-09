# Std Lib Imports
pass

# 3rd Party Imports
import discord
from discord.ext import commands
import valve.source.a2s
import valve.rcon

# Local Imports
from utils import load_config

global_config = load_config()
config = global_config.cogs.servers


class Servers(commands.Cog):

    @commands.command(aliases=config.usserver.aliases, help=config.usserver.help)
    @commands.has_any_role(*config.usserver.role_names)
    async def usserver(self, ctx):
        embed = await self.server_lookup("us.tf2maps.net")
        await ctx.send(embed=embed)

    @commands.command(aliases=config.euserver.aliases, help=config.euserver.help)
    @commands.has_any_role(*config.euserver.role_names)
    async def euserver(self, ctx):
        embed = await self.server_lookup("eu.tf2maps.net")
        await ctx.send(embed=embed)

    @staticmethod
    async def server_lookup(host):
        with valve.source.a2s.ServerQuerier((host, 27015)) as server:
            info = server.info()

        player_count = f"{info['player_count']}/{info['max_players']}"

        embed = discord.Embed(
            description=f"**steam://connect/{host}:27015**"
        )
        embed.set_author(name=info['server_name'], icon_url=global_config.cogs.search.tf2m_icon)
        embed.add_field(name="Current Map", value=info['map'], inline=True)
        embed.add_field(name="Player Count", value=player_count, inline=True)
        embed.set_footer(text=global_config.bot_footer)

        return embed
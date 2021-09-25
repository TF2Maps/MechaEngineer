# Std Lib Imports
pass

# 3rd Party Imports
import discord
from discord.ext.commands import Cog, command, has_any_role
import valve.source.a2s

# Local Imports
from utils import load_config, get_srcds_server_info, cog_error_handler
from utils.emojis import success, warning, error, info, loading
from utils.discord import not_nobot_role

global_config = load_config()
config = global_config.cogs.servers


class Servers(Cog):
    cog_command_error = cog_error_handler

    @command(aliases=config.usserver.aliases, help=config.usserver.help)
    @has_any_role(*config.usserver.role_names)
    @not_nobot_role()
    async def usserver(self, ctx):
        server = get_srcds_server_info("us.tf2maps.net")
        embed = await self.get_server_embed(server, "us.tf2maps.net")
        await ctx.send(embed=embed)

    @command(aliases=config.euserver.aliases, help=config.euserver.help)
    @has_any_role(*config.euserver.role_names)
    @not_nobot_role()
    async def euserver(self, ctx):
        server = get_srcds_server_info("eu.tf2maps.net")
        embed = await self.get_server_embed(server, "eu.tf2maps.net")
        await ctx.send(embed=embed)

    @command(aliases=config.active.aliases, help=config.active.help)
    @has_any_role(*config.active.role_names)
    @not_nobot_role()
    async def active(self, ctx):
        alive = False

        us_server = get_srcds_server_info("us.tf2maps.net")
        if us_server.player_count > config.active.player_threshold:
            embed = await self.get_server_embed(us_server, "us.tf2maps.net")
            await ctx.send(embed=embed)
            alive = True

        eu_server = get_srcds_server_info("eu.tf2maps.net")
        if eu_server.player_count > config.active.player_threshold:
            embed = await self.get_server_embed(eu_server, "eu.tf2maps.net")
            await ctx.send(embed=embed)
            alive = True

        if not alive:
            await ctx.send(f"{warning} No map tests are currently happening right now. Check back later")

    @staticmethod
    async def get_server_embed(server_data, host):
        player_count = f"{server_data.player_count}/{server_data.max_players}"

        embed = discord.Embed(
            description=f"**steam://connect/{host}:27015**"
        )
        embed.set_author(name=server_data.server_name, icon_url=global_config.icons.tf2m_icon)
        embed.add_field(name="Current Map", value=server_data.map_name, inline=True)
        embed.add_field(name="Player Count", value=player_count, inline=True)
        embed.set_footer(text=global_config.bot_footer)

        return embed
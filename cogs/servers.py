# Std Lib Imports
import socket
from datetime import datetime

# 3rd Party Imports
import discord
from discord.ext import tasks
from discord.ext.commands import Cog, slash_command
import asyncio
#import valve.source.a2s

# Local Imports
from utils import load_config, get_srcds_server_info, cog_error_handler
from utils.emojis import success, warning, error, info, loading
from utils.discord import not_nobot_role_slash, roles_required

global_config = load_config()
config = global_config.cogs.servers
server_info = global_config.server_info


class Servers(Cog):
    cog_command_error = cog_error_handler

    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        channel = self.bot.get_channel(config.server_embed_channel_id)
        self.us_server_embed_message = channel.get_partial_message(config.us_server_message_id)
        self.eu_server_embed_message = channel.get_partial_message(config.eu_server_message_id)
        self.us2_server_embed_message = channel.get_partial_message(config.us_central_message_id)
        self.server_embed.start()

        #for starting a new embed
        #await channel.send("** **")

    @tasks.loop(seconds=config.server_embed_interval)
    async def server_embed(self):
        try:
            server, players = await get_srcds_server_info("us.tf2maps.net", 27015)
            embed = await self.get_server_embed(server, "us.tf2maps.net", 'imp', player_data=players)
            await self.us_server_embed_message.edit(embed=embed)
        except asyncio.TimeoutError:
            try:
                server, players = await get_srcds_server_info("us.tf2maps.net", 27016)
                embed = await self.get_server_embed(server, "us.tf2maps.net", 'mvm', player_data=players)
                await self.eu_server_embed_message.edit(embed=embed)
            except asyncio.TimeoutError:
                embed = await self.get_server_offline_embed("us.tf2maps.net")
                await self.eu_server_embed_message.edit(embed=embed)

        try:
            server, players = await get_srcds_server_info("eu.tf2maps.net", 27015)
            embed = await self.get_server_embed(server, "eu.tf2maps.net", 'imp', player_data=players)
            await self.eu_server_embed_message.edit(embed=embed)
        except asyncio.TimeoutError:
            try:
                server, players = await get_srcds_server_info("eu.tf2maps.net", 27016)
                embed = await self.get_server_embed(server, "eu.tf2maps.net", 'mvm', player_data=players)
                await self.eu_server_embed_message.edit(embed=embed)
            except asyncio.TimeoutError:
                embed = await self.get_server_offline_embed("eu.tf2maps.net")
                await self.eu_server_embed_message.edit(embed=embed)

        try:
            server, players = await get_srcds_server_info("us-central.tf2maps.net", 27015)
            embed = await self.get_server_embed(server, "us_central.tf2maps.net", 'comp', player_data=players)
            await self.us2_server_embed_message.edit(embed=embed)
        except asyncio.TimeoutError:
            embed = await self.get_server_offline_embed("us-central.tf2maps.net")
            await self.us2_server_embed_message.edit(embed=embed)


    # ------------------
    # US Region Commands
    # ------------------
    @slash_command(
        name="us", 
        description=config.usserver.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.usserver.role_names),
            not_nobot_role_slash()
        ]
    )
    async def usserver(self, ctx):
        await ctx.defer()
        try:
            server, players = await get_srcds_server_info("us.tf2maps.net", 27015)
            embed = await self.get_server_embed(server, "us.tf2maps.net", 'imp')
            await ctx.respond(embed=embed)
        except socket.timeout:
            embed = await self.get_server_offline_embed("us.tf2maps.net")
            await ctx.respond(embed=embed)

    @slash_command(
        name="usmvm", 
        description=config.usmvm.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.usmvm.role_names),
            not_nobot_role_slash()
        ]
    )
    async def usmvm(self, ctx):
        await ctx.defer()
        try:
            server, players = await get_srcds_server_info("us.tf2maps.net", 27016)
            embed = await self.get_server_embed(server, "us.tf2maps.net", 'mvm')
            await ctx.respond(embed=embed)
        except socket.timeout:
            embed = await self.get_server_offline_embed("us.tf2maps.net")
            await ctx.respond(embed=embed)

    # ------------------
    # EU Region Commands
    # ------------------
    @slash_command(
        name="eu", 
        description=config.euserver.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.euserver.role_names),
            not_nobot_role_slash()
        ]
    )
    async def euserver(self, ctx):
        await ctx.defer()
        try:
            server, players = await get_srcds_server_info("eu.tf2maps.net", 27015)
            embed = await self.get_server_embed(server, "eu.tf2maps.net", 'imp')
            await ctx.respond(embed=embed)
        except socket.timeout:
            embed = await self.get_server_offline_embed("eu.tf2maps.net")
            await ctx.respond(embed=embed)
    
    @slash_command(
        name="eumvm", 
        description=config.eumvm.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.eumvm.role_names),
            not_nobot_role_slash()
        ]
    )
    async def eumvm(self, ctx):
        await ctx.defer()
        try:
            server, players = await get_srcds_server_info("eu.tf2maps.net", 27016)
            embed = await self.get_server_embed(server, "eu.tf2maps.net", 'mvm')
            await ctx.respond(embed=embed)
        except socket.timeout:
            embed = await self.get_server_offline_embed("eu.tf2maps.net")
            await ctx.respond(embed=embed)

    @slash_command(
        name="active", 
        description=config.active.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.active.role_names),
            not_nobot_role_slash()
        ]
    )
    async def active(self, ctx):
        await ctx.defer()
        alive = False
 
        try:
            us_server, us_players = await get_srcds_server_info("us.tf2maps.net", 27015)
            if us_server.player_count > config.active.player_threshold:
                embed = await self.get_server_embed(us_server, "us.tf2maps.net", 'imp')
                await ctx.respond(embed=embed)
                alive = True

            eu_server, eu_players = await get_srcds_server_info("eu.tf2maps.net", 27015)
            if eu_server.player_count > config.active.player_threshold:
                embed = await self.get_server_embed(eu_server, "eu.tf2maps.net", 'imp')
                await ctx.respond(embed=embed)
                alive = True

            if not alive:
                await ctx.respond(f"{warning} No map tests are currently happening right now. Check back later")
        except socket.timeout:
            await ctx.respond('A server is offline. Please use /eu or /us for the time being.')

    @staticmethod
    async def get_server_embed(server_data, host, type, player_data=None):
        player_count = f"{server_data.player_count}/{server_data.max_players}"

        thumbnail = None
        if host.startswith("us"):
            thumbnail = config.us_server_thumbnail
        elif host.startswith("eu"):
            thumbnail = config.eu_server_thumbnail

        server_obj = server_info[str(host).replace('.','_')]

        embed = discord.Embed(
            description=f"**Link: {server_obj[type].game_url} \n IP: {server_obj[type].ip}:{server_obj[type].port} \n STV: {server_obj[type].stv_url} **",
            timestamp=datetime.now()
        )
        embed.set_author(name=server_data.server_name, icon_url=global_config.icons.tf2m_icon)
        embed.add_field(name="Current Map", value=server_data.map_name, inline=True)
        embed.add_field(name="Player Count", value=player_count, inline=True)

        if server_data.player_count > 0 and player_data:
            players = [player.name if not player.name == "" else "CONNECTING..." for player in player_data ]
            players = "\n".join(players)
            embed.add_field(name="Players", value=f"```\n{players}```", inline=False)

        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text=global_config.bot_footer)

        return embed

    @staticmethod
    async def get_server_offline_embed(host):

        thumbnail = None
        if host.startswith("us"):
            thumbnail = config.us_server_thumbnail
        elif host.startswith("eu"):
            thumbnail = config.eu_server_thumbnail

        embed = discord.Embed(
            description=f"Server is currently offline",
            timestamp=datetime.now(),
            colour=discord.Colour.red()
        )
        embed.set_author(name=host, icon_url=global_config.icons.tf2m_icon)

        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text=global_config.bot_footer)

        return embed        

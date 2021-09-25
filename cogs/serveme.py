# Std Lib Imports
from urllib.parse import urlparse
import re
import os
from datetime import datetime

# 3rd Party Imports
import discord
from discord.ext.commands import Cog, command, has_any_role
import boto3
import httpx
from bs4 import BeautifulSoup
import imgkit

# Local Imports
from utils import load_config, cog_error_handler
from utils.emojis import success, warning, error, info, loading
from utils import get_random_password, wait_for_tcp, Timehash, readable_time
from utils.aws import create_server, get_instance_ip, region_to_location, list_servers, ec2_tags_to_dict
from utils.discord import not_nobot_role

global_config = load_config()
config = global_config.cogs.serveme


class ServeMe(Cog):
    cog_command_error = cog_error_handler

    @Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if not re.match("^https?://logs.tf/[0-9]+/?", message.content):
            return

        await message.channel.trigger_typing()

        url = message.content
        parsed_url = urlparse(url)

        async with httpx.AsyncClient() as client:
            response = await client.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')

        player_table = soup.select_one("#log-section-players").select_one("#players")
        table_height = 0
        for row in player_table.select_one("tbody").find_all("tr"):
            name = row.select_one(".log-player-name a.dropdown-toggle").text
            nclasses = len(row.select(".log-classes i"))

            if len(name) > 25 or nclasses > 4:
                table_height += 48
            else:
                table_height += 29

        options = {
            "xvfb": "",
            'crop-h': table_height + 28 + 30 + 66 + 10 + 28,
            'crop-w': '980',
            'crop-x': '178',
            'crop-y': '201',
        }

        filename = parsed_url.path.replace("/", "")
        filepath = f"/tmp/{filename}.png"

        imgkit.from_url(url, filepath, options=options)
        await message.edit(suppress=True)
        await message.reply(file=discord.File(filepath))
        os.remove(filepath)

    @command(aliases=config.shutdown.aliases, help=config.shutdown.help)
    @has_any_role(*config.shutdown.role_names)
    async def shutdown(self, ctx, request_id):
        raise NotImplementedError

    @command(aliases=config.serverlist.aliases, help=config.serverlist.help)
    @has_any_role(*config.serverlist.role_names)
    async def serverlist(self, ctx):
        await ctx.trigger_typing()
        servers = list_servers()

        if len(servers) == 0:
            await ctx.send(f"{error} There are no ad-hoc servers running right now.")
            return

        name_column = ""
        uptime_column = ""
        location_column = ""

        for server in servers:
            if not server.state['Name'] == "running":
                continue

            tags = ec2_tags_to_dict(server.tags)
            elapsed = int(datetime.now().timestamp() - server.launch_time.timestamp())
            uptime = readable_time(elapsed)

            name_column += tags['Name'] + "\n"
            uptime_column += uptime + "\n"
            location_column += tags['location'] + "\n"

        embed = discord.Embed()
        embed.add_field(name="Name", value=name_column, inline=True)
        embed.add_field(name="Uptime", value=uptime_column, inline=True)
        embed.add_field(name="Location", value=location_column, inline=True)
        embed.set_author(name="Running Ad-Hoc Servers", icon_url=global_config.icons.tf2m_icon)
        embed.set_footer(text=global_config.bot_footer)

        await ctx.send(embed=embed)

    @command(aliases=config.serveme.aliases, help=config.serveme.help)
    @has_any_role(*config.serveme.role_names)
    async def serveme(self, ctx, region="us-east-2"):

        # Setup Variables
        password = get_random_password()
        ttl = 180
        requester_name = ctx.author.name
        location = region_to_location(region)
        request_id = f"{get_random_password(2).upper()}{Timehash.now()}"

        # Create Server
        embed = self.get_serveme_embed("Requesting a new server...", ttl, location, request_id, "...", global_config.icons.loading_icon)
        message = await ctx.send(embed=embed)
        server = create_server(
            server_type="tf2-competitive",
            requester_name=requester_name,
            request_id=request_id,
            password=password,
            ttl=ttl,
            discord_channel_id=ctx.channel.id,
            discord_message_id=message.id,
            region=region
        )

        # Wait for server to boot
        embed = self.get_serveme_embed("Waiting for Team Fortress 2 to start up...", ttl, location, request_id, "...", global_config.icons.loading_icon)
        await message.edit(embed=embed)
        ip_address = get_instance_ip(server['InstanceId'], region=region)
        await wait_for_tcp(ip_address, 27015)

        # Ready!
        connect_info = (
            "```nginx\n"
            f"connect {ip_address}; password {password}\n"
            "```"
        )
        embed = self.get_serveme_embed("Server is ready!", ttl, location, request_id, connect_info, global_config.icons.tf2m_icon)
        await message.edit(embed=embed)


    @staticmethod
    def get_serveme_embed(title, ttl, location, request_id, connect_info, icon):
        embed = discord.Embed()
        embed.add_field(name="Connect Info", value=f"{connect_info}\n", inline=False)
        embed.add_field(name="Time Limit", value=f"{ttl} minutes", inline=True)
        embed.add_field(name="Location", value=location, inline=True)
        embed.add_field(name="Request ID", value=request_id, inline=True)
        embed.set_author(name=title, icon_url=icon)
        embed.set_footer(text=global_config.bot_footer)

        return embed

    @staticmethod
    def get_serverlist_embed(title, ttl, location, request_id, connect_info, icon):
        embed = discord.Embed()
        embed.add_field(name="Connect Info", value=f"{connect_info}\n", inline=False)
        embed.add_field(name="Time Limit", value=f"{ttl} minutes", inline=True)
        embed.add_field(name="Location", value=location, inline=True)
        embed.add_field(name="Request ID", value=request_id, inline=True)
        embed.set_author(name=title, icon_url=icon)
        embed.set_footer(text=global_config.bot_footer)

        return embed
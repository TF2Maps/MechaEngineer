# Std Lib Imports
import asyncio
import re
import tempfile
import os.path
from urllib.parse import urlparse
from datetime import datetime

# 3rd Party Imports
import asyncssh
from bs4 import BeautifulSoup
from discord.ext import commands
import discord
import httpx

# Local Imports
from utils import load_config, connect_db
from emojis import success, warning, error, info, loading
from models import Maps

global_config = load_config()
config = global_config.cogs.maplist


class MapList(commands.Cog):

    @commands.command(aliases=config.add.aliases, help=config.add.help)
    @commands.has_any_role(*config.add.role_names)
    async def add(self, ctx, link, *, notes=""):
        message = await ctx.reply(f"{loading} Uploading map to servers...")

        # Find map download in link
        link = await self.parse_link(link)
        await message.edit(content=f"{loading} Found link: {link}")

        # Download Map
        async with httpx.AsyncClient() as client:
            response = await client.get(link)

            content_header = response.headers.get("content-disposition")
            matches = re.search("filename=\"([\w.]+)\"", content_header)
            filename = matches.group(1)
            tempdir = tempfile.mkdtemp()
            filepath = os.path.join(tempdir, filename)
            map_name = re.sub("\.bsp$", "", filename)

        # Check for dupe
        already_in_queue = await Maps.filter(map=map_name, status="pending").all()
        if len(already_in_queue) > 0:
            await message.edit(content=f"{error} `{map_name}` is already on the list!")
            return

        await message.edit(content=f"{loading} Found file name: `{filename}`. Downloading...")

        with open(filepath, "wb") as file:
            file.write(response.content)

        # Upload to servers
        await message.edit(content=f"{loading} Uploading `{filename}`...")

        await asyncio.gather(
            self.upload_map(filepath, **global_config.sftp.us_tf2maps_net),
            self.upload_map(filepath, **global_config.sftp.eu_tf2maps_net),
            # self.upload_map(filepath, **global_config.sftp.redirect_tf2maps_net),
        )

        # Insert map into DB
        await message.edit(content=f"{loading} Putting `{map_name}` into the map queue...")

        await Maps.create(
            discord_user_handle=f"{ctx.author.name}#{ctx.author.discriminator}",
            discord_user_id=ctx.author.id,
            map=map_name,
            url=link,
            status="pending",
            notes=notes,
            added=datetime.now()
        )

        await message.edit(content=f"{success} Uploaded `{map_name}` successfully! Ready for testing!")

    @commands.command(aliases=config.delete.aliases, help=config.delete.help)
    @commands.has_any_role(*config.delete.role_names)
    async def delete(self, ctx, map_name):
        maps = await Maps.filter(map__icontains=map_name, status="pending", discord_user_id=ctx.author.id).all()

        if len(maps) == 0:
            await ctx.send(f"{error} You don't have a map with that name on the list!")
        else:
            await maps[0].delete()
            await ctx.send(f"{success} Deleted `{maps[0].map}` from the list.")

    @commands.command(aliases=config.maps.aliases, help=config.maps.help)
    @commands.has_any_role(*config.maps.role_names)
    async def maps(self, ctx):
        # Show maps uploaded by message author
        mymaps = await Maps.filter(status="pending", discord_user_id=ctx.author.id).all()
        mymaps_output = [f"• {item.map}" for item in mymaps]
        mymaps_output = "\n".join(mymaps_output)

        allmaps = await Maps.filter(status="pending").all()
        allmaps_output = [f"• {item.map}" for item in allmaps]
        allmaps_output = allmaps_output[:5]
        allmaps_output = "\n".join(allmaps_output)

        footer = f'\n\nFor a full list of **{len(allmaps)}** maps, please visit https://bot.tf2maps.net/maplist.php'

        embed = discord.Embed(
            title='Map Testing Queue',
            url="https://bot.tf2maps.net/maplist.php",
            description="Current maps waiting to be played"
        )
        if len(mymaps) > 0:
            embed.add_field(name="Your Maps", value=mymaps_output, inline=False)
        embed.add_field(name="All Maps", value=allmaps_output + footer, inline=False)

        await ctx.send(embed=embed)

    @staticmethod
    async def upload_map(localfile, hostname, username, password, port, path):
        async with asyncssh.connect(hostname, username=username, password=password, known_hosts=None) as conn:
            async with conn.start_sftp_client() as sftp:
                file_exists = await sftp.exists(os.path.join(path, os.path.basename(localfile)))

                if not file_exists:
                    await sftp.put(localfile, path)

    @staticmethod
    async def parse_link(link):
        parsed_url = urlparse(link)

        if parsed_url.netloc == "tf2maps.net":
            # https://tf2maps.net/downloads/pullsnake.11004/
            if re.match("^/downloads/\w+\.\d+\/?$", parsed_url.path):
                async with httpx.AsyncClient() as client:
                    response = await client.get(link)
                soup = BeautifulSoup(response.text, 'html.parser')
                href = soup.select("label.downloadButton > a.inner")[0].get("href")

                return f"https://tf2maps.net/{href}"

            # https://tf2maps.net/downloads/pullsnake.11004/download?version=29169
            elif re.match("^/downloads/\w+\.\d+/download$", parsed_url.path):
                return link

            #TODO trap for broken links

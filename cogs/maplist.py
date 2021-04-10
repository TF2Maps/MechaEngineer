# Std Lib Imports
import asyncio
import re
import tempfile
import os.path
from urllib.parse import urlparse, quote
from datetime import datetime, timedelta
import shutil
import bz2

# 3rd Party Imports
import asyncssh
from bs4 import BeautifulSoup
from discord.ext import commands
import discord
import httpx
from tortoise.query_utils import Q

# Local Imports
from utils import load_config, cog_error_handler, get_srcds_server_info
from emojis import success, warning, error, info, loading
from models import Maps

global_config = load_config()
config = global_config.cogs.maplist


class MapList(commands.Cog):
    cog_command_error = cog_error_handler

    @commands.command(aliases=config.add.aliases, help=config.add.help)
    @commands.has_any_role(*config.add.role_names)
    async def add(self, ctx, link, *, notes=""):
        message = await ctx.reply(f"{loading} Working on it...")

        if not re.match("https?://", link):
            search = ctx.bot.get_cog("Search")
            link = await search.search_downloads(link, discord_user_id=ctx.author.id)
            if not link:
                await message.edit(content=f"{error} You have to use a hyperlink.")
                await ctx.send_help(ctx.command)
                return
            else:
                if len(link) > 1:
                    await message.edit(content=f"{error} Found multiple links. Try a more specific link.")
                    return
                link = link[0]

        # Find map download in link
        link = await self.parse_link(link)
        if not link:
            await message.edit(content=f"{error} No valid link found.")
            await ctx.send_help(ctx.command)
            return

        await message.edit(content=f"{loading} Found link: {link}")

        # Get map info
        filename = await self.get_download_filename(link)
        filepath = os.path.join(tempfile.mkdtemp(), filename)
        map_name = re.sub("\.bsp$", "", filename)

        # Check for dupe
        already_in_queue = await Maps.filter(map=map_name, status="pending").all()
        if len(already_in_queue) > 0:
            await message.edit(content=f"{error} `{map_name}` is already on the list!")
            return

        # Download the map
        await message.edit(content=f"{loading} Found file name: `{filename}`. Downloading...")
        await self.download_file(link, filepath)

        # Upload to servers
        await message.edit(content=f"{loading} Uploading `{filename}` to game servers...")
        await asyncio.gather(
            self.upload_map(filepath, **global_config.sftp.us_tf2maps_net),
            self.upload_map(filepath, **global_config.sftp.eu_tf2maps_net),
        )

        # Compress and put on redirect
        await message.edit(content=f"{loading} Compressing `{filename}` for faster downloads...")
        compressed_file = self.compress_file(filepath)
        shutil.copyfile(
            compressed_file,
            os.path.join(
                global_config.sftp.redirect_tf2maps_net.path,
                os.path.basename(compressed_file)
            )
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

    @commands.command(aliases=config.update.aliases, help=config.update.help)
    @commands.has_any_role(*config.update.role_names)
    async def update(self, ctx, map_name, link, *, notes=""):
        maps = await Maps.filter(map__icontains=map_name, status="pending", discord_user_id=ctx.author.id).all()

        if len(maps) == 0:
            await ctx.send(f"{error} You don't have a map with that name on the list!")
        else:
            if link == "-":
                if not notes:
                    await ctx.reply(f"{error} Add a link or notes, otherwise theres nothing to update.")
                maps[0].notes = notes
                await maps[0].save()
                await ctx.reply(f"{success} Updated the notes for `{maps[0].map}`!")
            else:
                await maps[0].delete()
                await self.add(ctx, link, notes=notes)

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
        us_server = get_srcds_server_info("us.tf2maps.net")
        eu_server = get_srcds_server_info("eu.tf2maps.net")
        hour_ago = datetime.now() - timedelta(hours=1)

        live_maps = await Maps.filter(Q(map=us_server.map) | Q(map=eu_server.map), played__gte=hour_ago).all()
        maps = await Maps.filter(status="pending").all()

        map_names = ""
        for item in maps:
            if item.map in [i.map for i in live_maps]:
                continue
            else:
                map_names += f"• {item.map}\n"

        embed = discord.Embed(description=f"There are **{len(maps)}** maps waiting to be played.\nhttps://bot.tf2maps.net/maplist.php\n\u200b")
        embed.set_author(name=f"Map Testing Queue", url="https://bot.tf2maps.net/maplist.php", icon_url="https://cdn.discordapp.com/emojis/829026378078224435.png?v=1")

        if live_maps:
            live_map_names = "\n".join([i.map for i in live_maps])
            embed.add_field(name="Now Playing", value=live_map_names, inline=False)

        embed.add_field(name="Map Queue", value=map_names, inline=False)
        embed.set_footer(text=global_config.bot_footer)

        await ctx.send(embed=embed)

    @staticmethod
    def compress_file(filepath):
        output_filepath = f"{filepath}.bz2"

        with open(filepath, 'rb') as input:
            with bz2.BZ2File(output_filepath, 'wb') as output:
                shutil.copyfileobj(input, output)

        return output_filepath

    @staticmethod
    async def upload_map(localfile, hostname, username, password, port, path):
        async with asyncssh.connect(hostname, username=username, password=password, known_hosts=None) as conn:
            async with conn.start_sftp_client() as sftp:
                file_exists = await sftp.exists(os.path.join(path, os.path.basename(localfile)))

                if not file_exists:
                    await sftp.put(localfile, path)

    @staticmethod
    async def download_file(link, destination):
        async with httpx.AsyncClient() as client:
            response = await client.get(link)

            with open(destination, "wb") as file:
                file.write(response.content)

    @staticmethod
    async def get_download_filename(link):
        async with httpx.AsyncClient() as client:
            response = await client.head(link)
            content_header = response.headers.get("content-disposition")
            matches = re.search("filename=\"([\w.]+)\"", content_header)
            filename = matches.group(1)

            return filename

    @staticmethod
    async def parse_link(link):
        parsed_url = urlparse(link)

        if parsed_url.netloc == "tf2maps.net":
            # Example: https://tf2maps.net/downloads/pullsnake.11004/
            if re.match("^/(downloads|threads)/[\w\-]+\.\d+\/?$", parsed_url.path):
                async with httpx.AsyncClient() as client:
                    response = await client.get(link)
                soup = BeautifulSoup(response.text, 'html.parser')
                href = soup.select("label.downloadButton > a.inner")[0].get("href")

                return f"https://tf2maps.net/{href}"

            # Example: https://tf2maps.net/downloads/pullsnake.11004/download?version=29169
            elif re.match("^/downloads/\w+\.\d+/download$", parsed_url.path):
                return link


        # TODO Direct link
        # Example: http://maps.tf2.games/maps/jump_pyro_b1.bsp

        # TODO Dropbox link
        # Example: https://www.dropbox.com/s/6tyvkwc0af81k9e/pl_cactuscanyon_b1_test.bsp?dl=0

        # TODO Google Drive Link
        # Example: https://drive.google.com/file/d/17KXUZV7iHUL_A5pwOGNbVkbeCXUDIOgo/view?usp=sharing
        #          embeds link in page: https://drive.google.com/u/0/uc?id=17KXUZV7iHUL_A5pwOGNbVkbeCXUDIOgo&export=download
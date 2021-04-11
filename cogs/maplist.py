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
from discord.ext.commands import Cog, command, has_any_role
import discord
import httpx
from tortoise.query_utils import Q

# Local Imports
from utils import load_config, cog_error_handler, get_srcds_server_info
from utils.emojis import success, warning, error, info, loading
from utils.files import compress_file, download_file, get_download_filename, upload_file
from utils.search import search_downloads

from models import Maps

global_config = load_config()
config = global_config.cogs.maplist


class MapList(Cog):
    cog_command_error = cog_error_handler

    @command(aliases=config.add.aliases, help=config.add.help)
    @has_any_role(*config.add.role_names)
    async def add(self, ctx, link, *, notes=""):
        message = await ctx.reply(f"{loading} Adding your map...")
        await self.add_map(ctx, message, link, notes)

    @command(aliases=config.update.aliases, help=config.update.help)
    @has_any_role(*config.update.role_names)
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
                message = await ctx.reply(f"{loading} Updating your map...")
                await self.add_map(ctx, message, link, notes, update=True)

    @command(aliases=config.delete.aliases, help=config.delete.help)
    @has_any_role(*config.delete.role_names)
    async def delete(self, ctx, map_name):
        maps = await Maps.filter(map__icontains=map_name, status="pending", discord_user_id=ctx.author.id).all()

        if len(maps) == 0:
            await ctx.send(f"{error} You don't have a map with that name on the list!")
        else:
            await maps[0].delete()
            await ctx.send(f"{success} Deleted `{maps[0].map}` from the list.")


    @command(aliases=config.maps.aliases, help=config.maps.help)
    @has_any_role(*config.maps.role_names)
    async def maps(self, ctx):
        us_server = get_srcds_server_info("us.tf2maps.net")
        eu_server = get_srcds_server_info("eu.tf2maps.net")
        hour_ago = datetime.now() - timedelta(minutes=10)

        live_maps = await Maps.filter(Q(map=us_server.map) | Q(map=eu_server.map), played__gte=hour_ago).all()
        live_maps = [] # TODO why is this sometimes returning many entires?
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

    async def add_map(self, ctx, message, link, notes="", update=False):
        # If not link; use fuzzy search
        if not re.match("https?://", link):
            link = await search_downloads(link, discord_user_id=ctx.author.id)
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
        filename = await get_download_filename(link)
        filepath = os.path.join(tempfile.mkdtemp(), filename)
        map_name = re.sub("\.bsp$", "", filename)

        # Check for dupe
        already_in_queue = await Maps.filter(map=map_name, status="pending").all()
        if len(already_in_queue) > 0 and not update:
            await message.edit(content=f"{warning} `{map_name}` is already on the list!")
            return

        # Download the map
        await message.edit(content=f"{loading} Found file name: `{filename}`. Downloading...")
        await download_file(link, filepath)

        # Upload to servers
        await message.edit(content=f"{loading} Uploading `{filename}` to game servers...")
        await asyncio.gather(
            upload_file(filepath, **global_config.sftp.us_tf2maps_net),
            upload_file(filepath, **global_config.sftp.eu_tf2maps_net),
        )

        # Compress and put on redirect
        await message.edit(content=f"{loading} Compressing `{filename}` for faster downloads...")
        compressed_file = compress_file(filepath)
        redirect_path = os.path.join(global_config.sftp.redirect_tf2maps_net.path, os.path.basename(compressed_file))
        shutil.copyfile(compressed_file, redirect_path)

        # Insert map into DB
        await message.edit(content=f"{loading} Putting `{map_name}` into the map queue...")

        if update:
            existing_map = already_in_queue[0]
            existing_map.url = link
            if notes:
                existing_map.notes = notes
            await existing_map.save()
            await message.edit(content=f"{success} Updated `{map_name}` successfully! Ready for testing!")
        else:
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
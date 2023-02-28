import asyncio
import re
import aioboto3
import tempfile
import os.path
from urllib.parse import urlparse, quote
from datetime import datetime, timedelta
import shutil
import bz2
import hashlib

# 3rd Party Imports
import asyncssh
from bs4 import BeautifulSoup
from discord.ext.commands import Cog, slash_command
import discord
import httpx
from tortoise.expressions import Q

# Local Imports
from utils import load_config, cog_error_handler, get_srcds_server_info
from utils.emojis import success, warning, error, info, loading
from utils.files import compress_file, download_file, get_download_filename, upload_to_gameserver, upload_to_redirect, remote_file_exists, redirect_file_exists, check_redirect_hash
from utils.search import search_downloads, ForumUserNotFoundException
from utils.discord import not_nobot_role_slash, roles_required

from models import Maps

global_config = load_config()
config = global_config.cogs.maplist


class MapList(Cog):
    cog_command_error = cog_error_handler


    @slash_command(
        name="uploadcheck", 
        description=config.uploadcheck.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.uploadcheck.role_names),
            not_nobot_role_slash()
        ]
    )
    async def uploadcheck(self, ctx, map_name):
        await ctx.defer()

        us, eu, redirect = await asyncio.gather(
            remote_file_exists(f"{map_name}.bsp", **global_config.sftp.us_tf2maps_net),
            remote_file_exists(f"{map_name}.bsp", **global_config.sftp.eu_tf2maps_net),
            redirect_file_exists(f"{map_name}.bsp.bz2", global_config['vultr_s3_client']),
        )

        output = ""
        if us:
            output += f"{success} US Server\n"
        else:
            output += f"{error} US Server\n"
        if eu:
            output += f"{success} EU Server\n"
        else:
            output += f"{error} EU Server\n"
        if redirect:
            output += f"{success} Redirect Server"
        else:
            output += f"{error} Redirect Server"

        embed = discord.Embed(description=output)
        embed.set_author(name=f"Map Upload Status")
        embed.set_footer(text=global_config.bot_footer)

        await ctx.respond(embed=embed, content="")


    @slash_command(
        name="add", 
        description=config.add.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.add.role_names),
            not_nobot_role_slash()
        ]
    )
    async def add(self, ctx, link, *, notes=""):
        await ctx.defer()
        message = await ctx.respond(f"{loading} Adding your map...")
        await self.add_map(ctx, message, link, notes)

    @slash_command(
        name="update", 
        description=config.update.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.update.role_names),
            not_nobot_role_slash()
        ]
    )
    async def update(self, ctx, map_name, link, *, notes=""):
        await ctx.defer()
        maps = await Maps.filter(map__icontains=map_name, status="pending", discord_user_id=ctx.author.id).all()

        if len(maps) == 0:
            await ctx.respond(f"{error} You don't have a map with that name on the list!")
        else:
            if link == "-":
                if not notes:
                    await ctx.respond(f"{error} Add a link or notes, otherwise theres nothing to update.")
                maps[0].notes = notes
                await maps[0].save()
                await ctx.respond(f"{success} Updated the notes for `{maps[0].map}`!")
            else:
                message = await ctx.respond(f"{loading} Updating your map...")
                await self.add_map(ctx, message, link, notes, old_map=maps[0])


    @slash_command(
        name="delete", 
        description=config.delete.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.delete.role_names),
            not_nobot_role_slash()
        ]
    )
    async def delete(self, ctx, map_name):
        await ctx.defer()
        maps = []
        override_roles = set(config.delete.override_roles)
        user_roles = set([role.name for role in ctx.author.roles])

        override = len(override_roles.intersection(user_roles)) > 0

        if override:
            maps = await Maps.filter(map__icontains=map_name, status="pending").all()
        else:
            maps = await Maps.filter(map__icontains=map_name, status="pending", discord_user_id=ctx.author.id).all()

        if len(maps) == 0:
            await ctx.respond(f"{error} You don't have a map with that name on the list!")
        else:
            await maps[0].delete()
            await ctx.respond(f"{success} Deleted `{maps[0].map}` from the list.")


    @slash_command(
        name="maps", 
        description=config.maps.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.maps.role_names),
            not_nobot_role_slash()
        ]
    )
    async def maps(self, ctx):
        # us_server = get_srcds_server_info("us.tf2maps.net")
        # eu_server = get_srcds_server_info("eu.tf2maps.net")
        # hour_ago = datetime.now() - timedelta(minutes=10)

        # live_maps = await Maps.filter(Q(map=us_server.map) | Q(map=eu_server.map), played__gte=hour_ago).all()
        await ctx.defer()
        live_maps = [] # TODO why is this sometimes returning many entires?
        maps = await Maps.filter(status="pending").all()

        map_names = ""
        for item in maps:
            if item.map in [i.map for i in live_maps]:
                continue
            else:
                map_names += f"• {item.map}\n"

        embed = discord.Embed(description=f"There are **{len(maps)}** maps waiting to be played.\nhttps://bot.tf2maps.net/maplist\n\u200b")
        embed.set_author(name=f"Map Testing Queue", url="https://bot.tf2maps.net/maplist", icon_url="https://cdn.discordapp.com/emojis/829026378078224435.png?v=1")

        if live_maps:
            live_map_names = "\n".join([i.map for i in live_maps])
            embed.add_field(name="Now Playing", value=live_map_names, inline=False)

        embed.add_field(name="Map Queue", value=map_names, inline=False)
        embed.set_footer(text=global_config.bot_footer)

        await ctx.respond(embed=embed)

    async def add_map(self, ctx, message, link, notes="", old_map=None):
        # If not link; use fuzzy search
        if not re.match("https?://", link):
            try:
                link = await search_downloads(link, discord_user_id=ctx.author.id)
            except ForumUserNotFoundException:
                await message.edit(content=f"{error} You either need to provide a link or need to connect your TF2Maps.net account to Discord. See <#{global_config.faq_channel_id}>")
                return

            if not link:
                await message.edit(content=f"{error} Could not find a download by the name. Try using a link instead.")
                return
            else:
                if len(link) > 1:
                    await message.edit(content=f"{error} Found multiple links. Use a more specific link.")
                    return
                link = link[0]

        # Find map download in link
        try:
            link = await self.parse_link(link)
        except IndexError:
            await message.edit(content=f"{error} External Links not currently supported. Upload your map directly to the website.")
            return

        if not link:
            await message.edit(content=f"{error} No valid link found.")
            return

        await message.edit(content=f"{loading} Found link: {link}")

        # Get map info
        filename = await get_download_filename(link)
        filepath = os.path.join(tempfile.mkdtemp(), filename)
        map_name = re.sub("\.bsp$", "", filename)
        
        # Must be a BSP
        if not re.search("\.bsp$", filename):
            await message.edit(content=f"{warning} `{map_name}` is not a BSP!")
            return

        # Check for dupe
        already_in_queue = await Maps.filter(map=map_name, status="pending").all()
        if len(already_in_queue) > 0 and not old_map:
            await message.edit(content=f"{warning} `{map_name}` is already on the list!")
            return

        # Download the map
        await message.edit(content=f"{loading} Found file name: `{filename}`. Downloading...")
        await download_file(link, filepath)
        
        # Compress file for redirect
        await message.edit(content=f"{loading} Compressing `{filename}` for faster downloads...")
        compressed_file = compress_file(filepath)

        # Ensure map has the same MD5 sum as an existing one
        if await redirect_file_exists(compressed_file, global_config['vultr_s3_client']):
            if not await check_redirect_hash(compressed_file, global_config['vultr_s3_client']):
                await message.edit(content=f"{warning} Your map `{map_name}` differs from the map on the server. Please upload a new version of the map.")
                return

        # Upload to servers
        await message.edit(content=f"{loading} Uploading `{filename}` to servers...")
        await asyncio.gather(
            upload_to_gameserver(filepath, **global_config.sftp.us_tf2maps_net),
            upload_to_gameserver(filepath, **global_config.sftp.eu_tf2maps_net),
            upload_to_redirect(compressed_file, global_config['vultr_s3_client'])
        )

        # Insert map into DB
        await message.edit(content=f"{loading} Putting `{map_name}` into the map queue...")

        if not contains_version_number(map_name):
            version_warning = f"\n\n{warning} Your map seems to not include a version number. You must include a version number for your map to be tested."\
                "\nThe map was still uploaded. You can use `/update` to replace it with a verision that includes a proper version number. If you did "\
                "include one, disregard this message"
        else:
            version_warning = ""

        if old_map:
            old_map.url = link
            old_map.map = map_name
            if notes:
                old_map.notes = notes
            await old_map.save()
            await message.edit(content=f"{success} Updated `{map_name}` successfully! Ready for testing!{version_warning}")
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
            await message.edit(content=f"{success} Uploaded `{map_name}` successfully! Ready for testing!{version_warning}")


    @staticmethod
    async def parse_link(link):
        parsed_url = urlparse(link)

        matched_link = None
        if parsed_url.netloc == "tf2maps.net" or parsed_url.netloc == "www.tf2maps.net":
            # Example: https://tf2maps.net/downloads/pullsnake.11004/
            if re.match("^/(downloads|threads)/[\w\-]+\.\d+\/?$", parsed_url.path):
                async with httpx.AsyncClient() as client:
                    response = await client.get(link, follow_redirects=True)
                soup = BeautifulSoup(response.text, 'html.parser')
                href = soup.select(".button--icon--download")[0].get("href")

                matched_link = f"https://tf2maps.net/{href}"

            # Example: https://tf2maps.net/downloads/pullsnake.11004/download?version=29169
            elif re.match("^/downloads/\w+\.\d+/download$", parsed_url.path):
                matched_link = link

        async with httpx.AsyncClient() as client:
            response = await client.head(link, follow_redirects=True)
            redir = urlparse(str(response.url))

            # Example: https://www.dropbox.com/s/6tyvkwc0af81k9e/pl_cactuscanyon_b1_test.bsp?dl=0
            if redir.netloc == "dropbox.com" or redir.netloc == "www.dropbox.com":
                matched_link = str(response.url).replace("dl=0", "dl=1")

        return matched_link

        # TODO Direct link
        # Example: http://maps.tf2.games/maps/jump_pyro_b1.bsp

        # TODO Google Drive Link
        # Example: https://drive.google.com/file/d/17KXUZV7iHUL_A5pwOGNbVkbeCXUDIOgo/view?usp=sharing
        #          embeds link in page: https://drive.google.com/u/0/uc?id=17KXUZV7iHUL_A5pwOGNbVkbeCXUDIOgo&export=download

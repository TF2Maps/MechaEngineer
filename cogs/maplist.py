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
import zipfile
import aiohttp
import time
import urllib3
import requests

# 3rd Party Imports
import asyncssh
from bs4 import BeautifulSoup
from discord.ext.commands import Cog, slash_command
import discord
import httpx
from tortoise.expressions import Q
import botocore

# Local Imports
from utils import load_config, cog_error_handler, get_srcds_server_info
from utils.emojis import success, warning, error, info, loading
from utils.files import compress_file, download_file, get_download_filename, upload_to_gameserver, upload_to_redirect, remote_file_exists, redirect_file_exists, check_redirect_hash, dropbox_download, remote_file_size
from utils.search import search_downloads, ForumUserNotFoundException
from utils.discord import not_nobot_role_slash, roles_required
from utils.hdr_check import bsp_validate_hdr

from models import Maps

global_config = load_config()
config = global_config.cogs.maplist


class MapList(Cog):
    cog_command_error = cog_error_handler

    @slash_command(
        name="uploadmvm",
        description=config.uploadmvm.help,
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.uploadmvm.role_names),
            not_nobot_role_slash()
        ]
    )
    async def uploadmvm(self, ctx, file: discord.Attachment):
        await ctx.defer()

        # Make temp dir
        message = await ctx.respond(f"{loading} Making temp dir for zip")

        tempdir = tempfile.mkdtemp()
        tempfilepath = os.path.join(tempdir, file.filename)

        # save zip to /tmp/randomletters/zipname.zip
        await message.edit(content=f"{loading} Downloading `{file.filename}`...")
        await file.save(tempfilepath)

        # Unzip
        await message.edit(content=f"{loading} Unzipping `{file.filename}`...")
        with zipfile.ZipFile(tempfilepath, "r") as zip:
            zip.extractall(tempdir)

        upload_futures = []

        # Get all BSP files contained within
        for file in os.listdir(tempdir):
            filepath = os.path.join(tempdir, file)

            if not filepath.endswith('.zip'):

                # lets try something new NOW THE FILES CAN BE ANYWHERE
                for dirname, dirs, files in os.walk(filepath):
                    for filename in files:
                        filename_without_extension, extension = os.path.splitext(
                            filename)
                        if extension == '.bsp':
                            bsp_filepath = dirname + '/' + filename

                            # Compress with bzip2
                            await message.edit(content=f"{loading} Compressing `{filename}`...")
                            compressed_file = compress_file(
                                os.path.join(dirname, filename))

                            upload_futures.extend([
                                upload_to_redirect(
                                    compressed_file, global_config['vultr_s3_client']),
                                upload_to_gameserver(bsp_filepath, global_config.sftp.mvm.us_tf2maps_net.hostname, global_config.sftp.mvm.us_tf2maps_net.username,
                                                     global_config.sftp.mvm.us_tf2maps_net.password, global_config.sftp.mvm.us_tf2maps_net.port, global_config.sftp.mvm.us_tf2maps_net.mapspath),
                                upload_to_gameserver(bsp_filepath, global_config.sftp.mvm.eu_tf2maps_net.hostname, global_config.sftp.mvm.eu_tf2maps_net.username,
                                                     global_config.sftp.mvm.eu_tf2maps_net.password, global_config.sftp.mvm.eu_tf2maps_net.port, global_config.sftp.mvm.eu_tf2maps_net.mapspath),
                            ])

                        # population files
                        if extension == '.pop':
                            pop_filepath = dirname + '/' + filename
                            upload_futures.extend([
                                upload_to_gameserver(pop_filepath, global_config.sftp.mvm.us_tf2maps_net.hostname, global_config.sftp.mvm.us_tf2maps_net.username,
                                                     global_config.sftp.mvm.us_tf2maps_net.password, global_config.sftp.mvm.us_tf2maps_net.port, global_config.sftp.mvm.us_tf2maps_net.poppath),
                                upload_to_gameserver(pop_filepath, global_config.sftp.mvm.eu_tf2maps_net.hostname, global_config.sftp.mvm.eu_tf2maps_net.username,
                                                     global_config.sftp.mvm.eu_tf2maps_net.password, global_config.sftp.mvm.eu_tf2maps_net.port, global_config.sftp.mvm.eu_tf2maps_net.poppath),
                            ])

                        # stuff for huds
                        if extension == '.res':
                            pop_filepath = dirname + '/' + filename
                            upload_futures.extend([
                                upload_to_gameserver(pop_filepath, global_config.sftp.mvm.us_tf2maps_net.hostname, global_config.sftp.mvm.us_tf2maps_net.username,
                                                     global_config.sftp.mvm.us_tf2maps_net.password, global_config.sftp.mvm.us_tf2maps_net.port, global_config.sftp.mvm.us_tf2maps_net.mapspath),
                                upload_to_gameserver(pop_filepath, global_config.sftp.mvm.eu_tf2maps_net.hostname, global_config.sftp.mvm.eu_tf2maps_net.username,
                                                     global_config.sftp.mvm.eu_tf2maps_net.password, global_config.sftp.mvm.eu_tf2maps_net.port, global_config.sftp.mvm.eu_tf2maps_net.mapspath),
                            ])

                        # particle manifests
                        if extension == '.txt':
                            if dirname.endswith('particles.txt'):
                                pop_filepath = dirname + '/' + filename
                                upload_futures.extend([
                                    upload_to_gameserver(pop_filepath, global_config.sftp.mvm.us_tf2maps_net.hostname, global_config.sftp.mvm.us_tf2maps_net.username,
                                                         global_config.sftp.mvm.us_tf2maps_net.password, global_config.sftp.mvm.us_tf2maps_net.port, global_config.sftp.mvm.us_tf2maps_net.mapspath),
                                    upload_to_gameserver(pop_filepath, global_config.sftp.mvm.eu_tf2maps_net.hostname, global_config.sftp.mvm.eu_tf2maps_net.username,
                                                         global_config.sftp.mvm.eu_tf2maps_net.password, global_config.sftp.mvm.eu_tf2maps_net.port, global_config.sftp.mvm.eu_tf2maps_net.mapspath),
                                ])

                        # the navigation file
                        if extension == '.nav':
                            nav_filepath = dirname + '/' + filename
                            upload_futures.extend([
                                upload_to_gameserver(nav_filepath, global_config.sftp.mvm.us_tf2maps_net.hostname, global_config.sftp.mvm.us_tf2maps_net.username,
                                                     global_config.sftp.mvm.us_tf2maps_net.password, global_config.sftp.mvm.us_tf2maps_net.port, global_config.sftp.mvm.us_tf2maps_net.navpath),
                                upload_to_gameserver(nav_filepath, global_config.sftp.mvm.eu_tf2maps_net.hostname, global_config.sftp.mvm.eu_tf2maps_net.username,
                                                     global_config.sftp.mvm.eu_tf2maps_net.password, global_config.sftp.mvm.eu_tf2maps_net.port, global_config.sftp.mvm.eu_tf2maps_net.navpath),
                            ])

                        # we should check if it's in materials/hud/
                        if extension == '.vmt':
                            if dirname.endswith('/materials/hud/'):
                                vmt_filepath = dirname + '/' + filename
                                upload_futures.extend([
                                    upload_to_gameserver(vmt_filepath, global_config.sftp.mvm.us_tf2maps_net.hostname, global_config.sftp.mvm.us_tf2maps_net.username,
                                                         global_config.sftp.mvm.us_tf2maps_net.password, global_config.sftp.mvm.us_tf2maps_net.port, global_config.sftp.mvm.us_tf2maps_net.materialspath),
                                    upload_to_gameserver(vmt_filepath, global_config.sftp.mvm.eu_tf2maps_net.hostname, global_config.sftp.mvm.eu_tf2maps_net.username,
                                                         global_config.sftp.mvm.eu_tf2maps_net.password, global_config.sftp.mvm.eu_tf2maps_net.port, global_config.sftp.mvm.eu_tf2maps_net.materialspath),
                                ])

                        if extension == '.vtf':
                            if dirname.endswith('/materials/hud/'):
                                vtf_filepath = dirname + '/' + filename
                                upload_futures.extend([
                                    upload_to_gameserver(vtf_filepath, global_config.sftp.mvm.us_tf2maps_net.hostname, global_config.sftp.mvm.us_tf2maps_net.username,
                                                         global_config.sftp.mvm.us_tf2maps_net.password, global_config.sftp.mvm.us_tf2maps_net.port, global_config.sftp.mvm.us_tf2maps_net.materialspath),
                                    upload_to_gameserver(vtf_filepath, global_config.sftp.mvm.eu_tf2maps_net.hostname, global_config.sftp.mvm.eu_tf2maps_net.username,
                                                         global_config.sftp.mvm.eu_tf2maps_net.password, global_config.sftp.mvm.eu_tf2maps_net.port, global_config.sftp.mvm.eu_tf2maps_net.materialspath),
                                ])

        # Upload to us, eu and redirect
        await message.edit(content=f"{loading} Uploading maps...")
        await asyncio.gather(*upload_futures)
        await message.edit(content=f"{success} All maps uploaded successfully!")

    @slash_command(
        name="uploadzip",
        description=config.uploadzip.help,
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.uploadzip.role_names),
            not_nobot_role_slash()
        ]
    )
    async def uploadzip(self, ctx, file: discord.Attachment):
        await ctx.defer()

        # Make temp dir
        message = await ctx.respond(f"{loading} Making temp dir for zip")

        tempdir = tempfile.mkdtemp()
        tempfilepath = os.path.join(tempdir, file.filename)

        # Download Zip from discord into temp dir
        await message.edit(content=f"{loading} Downloading `{file.filename}`...")
        await file.save(tempfilepath)

        # Unzip maps
        await message.edit(content=f"{loading} Unzipping `{file.filename}`...")
        with zipfile.ZipFile(tempfilepath, "r") as zip:
            zip.extractall(tempdir)

        upload_futures = []

        # Get all BSP files contained within
        for file in os.listdir(tempdir):
            filepath = os.path.join(tempdir, file)
            if file.endswith(".bsp"):
                # Compress with bzip2
                await message.edit(content=f"{loading} Compressing `{file}`...")
                compressed_file = compress_file(os.path.join(tempdir, file))

                upload_futures.extend([
                    # upload_to_redirect(compressed_file, global_config['vultr_s3_client']),
                    upload_to_gameserver(
                        filepath, **global_config.sftp.us_tf2maps_net),
                    upload_to_gameserver(
                        filepath, **global_config.sftp.eu_tf2maps_net)
                ])

        # Upload to us, eu and redirect
        await message.edit(content=f"{loading} Uploading maps...")
        await asyncio.gather(*upload_futures)
        await message.edit(content=f"{success} All maps uploaded successfully!")

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

        try:
            r = requests.get(
                'https://sjc1.vultrobjects.com/tf2maps-maps/maps/1cp_seafoam_a1.bsp.bz2', timeout=4)
            master_redirect = await redirect_file_exists(f"{map_name}.bsp.bz2", global_config['vultr_s3_client']),
        except requests.exceptions.Timeout as e:
            master_redirect = False
        except Exception as e:
            master_redirect = False

        us_size, eu_size, us_redir_size, eu_redir_size = await asyncio.gather(
            remote_file_size(f"{map_name}.bsp", **
                             global_config.sftp.us_tf2maps_net),
            remote_file_size(f"{map_name}.bsp", **
                             global_config.sftp.eu_tf2maps_net),
            remote_file_size(f"{map_name}.bsp.bz2", **
                             global_config.sftp.us_fastdl),
            remote_file_size(f"{map_name}.bsp.bz2", **
                             global_config.sftp.eu_fastdl)
        )

        us, eu, us_redirect, eu_redirect = await asyncio.gather(
            remote_file_exists(f"{map_name}.bsp", **
                               global_config.sftp.us_tf2maps_net),
            remote_file_exists(f"{map_name}.bsp", **
                               global_config.sftp.eu_tf2maps_net),
            remote_file_exists(f"{map_name}.bsp.bz2", **
                               global_config.sftp.us_fastdl),
            remote_file_exists(f"{map_name}.bsp.bz2", **
                               global_config.sftp.eu_fastdl)
        )

        output = ""
        if us:
            output += f"{success} US Server - {round(us_size, 2)}MB\n"
        else:
            output += f"{error} US Server\n"
        if eu:
            output += f"{success} EU Server - {round(eu_size, 2)}MB\n"
        else:
            output += f"{error} EU Server\n"
        if us_redirect:
            output += f"{success} US Redirect Server - {round(us_redir_size, 2)}MB\n"
        else:
            output += f"{error} US Redirect Server\n"
        if eu_redirect:
            output += f"{success} EU Redirect Server - {round(eu_redir_size, 2)}MB\n"
        else:
            output += f"{error} EU Redirect Server\n"

        try:
            master_redirect = master_redirect[0]
        except:
            master_redirect = False
        if master_redirect:
            output += f"{success} Master Redirect Server\n"
        else:
            output += f"{error} Master Redirect Server\n"

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
    async def add(self, ctx,
                  link,
                  *,
                  randomcrits: discord.Option(input_type=str, description='Select if you want random crits.', choices=config.add.choices.crits, default='no', required=False),
                  region: discord.Option(input_type=str, description='Select what region you want the map tested in.', choices=config.add.choices.region, default='both', required=False),
                  notes=""):
        await ctx.defer()
        message = await ctx.respond(f"{loading} Adding your map...")
        await self.add_map(ctx, message, link, randomcrits, region, notes)

    @slash_command(
        name="update",
        description=config.update.help,
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.update.role_names),
            not_nobot_role_slash()
        ]
    )
    async def update(self,
                    ctx,
                    map_name,
                    link,
                    *,
                    randomcrits: discord.Option(input_type=str, description='Select if you want random crits.', choices=config.add.choices.crits, default='no', required=False),
                    region: discord.Option(input_type=str, description='Select what region you want the map tested in.', choices=config.add.choices.region, default='both', required=False),
                    notes=""):
        await ctx.defer()
        maps = await Maps.filter(map__icontains=map_name, status="pending", discord_user_id=ctx.author.id).all()

        if len(maps) == 0:
            await ctx.respond(f"{error} You don't have a map with that name on the list!")
        else:
            if link == "-":
                if not notes:
                    await ctx.respond(f"{error} Add a link or notes, otherwise theres nothing to update.")

                # standardize notes
                if region == "us":
                    notes = "US Only. " + notes
                if region == "eu":
                    notes = "EU Only. " + notes
                if randomcrits == "yes":
                    notes = "Random crits ON. " + notes

                maps[0].notes = notes
                await maps[0].save()
                await ctx.respond(f"{success} Updated the notes for `{maps[0].map}`!")
            else:
                message = await ctx.respond(f"{loading} Updating your map...")
                await self.add_map(ctx, message, link, randomcrits, region, notes, old_map=maps[0])

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
        live_maps = []  # TODO why is this sometimes returning many entires?
        maps = await Maps.filter(status="pending").all()

        if len(maps) > 35:
            await ctx.respond(f"There's {len(maps)} maps... https://bot.tf2maps.net/maplist")
            return

        map_names = ""
        for item in maps:
            if item.map in [i.map for i in live_maps]:
                continue
            else:
                map_names += f"• {item.map}\n"

        embed = discord.Embed(
            description=f"There are **{len(maps)}** maps waiting to be played.\nhttps://bot.tf2maps.net/maplist\n\u200b")
        embed.set_author(name=f"Map Testing Queue", url="https://bot.tf2maps.net/maplist",
                         icon_url="https://cdn.discordapp.com/emojis/829026378078224435.png?v=1")

        if live_maps:
            live_map_names = "\n".join([i.map for i in live_maps])
            embed.add_field(name="Now Playing",
                            value=live_map_names, inline=False)

        embed.add_field(name="Map Queue", value=map_names, inline=False)
        embed.set_footer(text=global_config.bot_footer)

        await ctx.respond(embed=embed)

    async def add_map(self, ctx, message, link, randomcrits, region, notes="", old_map=None):

        if region == "us":
            notes = "US Only. " + notes
        if region == "eu":
            notes = "EU Only. " + notes
        if randomcrits == "yes":
            notes = "Random crits ON. " + notes
            

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
        try:
            filename = await get_download_filename(link)
            filepath = os.path.join(tempfile.mkdtemp(), filename)
            map_name = re.sub("\.bsp$", "", filename)
        except TypeError as e:
            print(e)
            await message.edit(content=f"{warning} TypeError: Unable to be download! Is the site up? Is it an external download? Is there more than one download choice?")
            return

        # Must be a BSP
        if not re.search("\.bsp$", filename):
            await message.edit(content=f"{warning} `{map_name}` is not a BSP!")
            return

        # Must not contain uppercase letters
        if re.search("[A-Z]", map_name):
            await message.edit(content=f"{error} `{map_name}.bsp` contains uppercase letters! Aborting!")
            return

        # must not contain special characters
        if re.search("[^A-Z_a-z0-9]", map_name):
            await message.edit(content=f"{error} `{map_name}.bsp` contains special characters! Aborting!")
            return

        # Check for dupe
        already_in_queue = await Maps.filter(map=map_name, status="pending").all()
        if len(already_in_queue) > 0 and not old_map:
            await message.edit(content=f"{warning} `{map_name}` is already on the list!")
            return

        # stopped working, blocking for now
        if str(link).startswith('https://www.dropbox.com' or 'https://dropbox.com'):
            # await dropbox_download(link, filepath)
            await message.edit(content=f"{error} No valid link found. Make sure it's uploaded to TF2maps.net.")
            return

        # Download the map
        await message.edit(content=f"{loading} Found file name: `{filename}`. Downloading...")

        if str(link).startswith('https://www.dropbox.com' or 'https://dropbox.com'):
            # await dropbox_download(link, filepath)

            filesize = os.stat(filepath)
            if filesize.st_size < 900000:
                await message.edit(content=f"{error} `{filename}` is not larger than 1mb, is it able to be downloaded?")
                return
        else:
            await download_file(link, filepath)

        # Check map for HDR lighting issues
        print(bsp_validate_hdr(filepath))
        bsp_error = bsp_validate_hdr(filepath)
        if bsp_error[0] == False:
            await message.edit(content=f"{error} `{filename}` {bsp_error[1]}")
            return

        # Compress file for redirect
        await message.edit(content=f"{loading} Compressing `{filename}` for faster downloads...")
        compressed_file = compress_file(filepath)

        # getting stuck here
        # except ServerTimeoutError:
        try:
            r = requests.get(
                'https://sjc1.vultrobjects.com/tf2maps-maps/maps/1cp_seafoam_a1.bsp.bz2', timeout=4)
            # Ensure map has the same MD5 sum as an existing one
            if await redirect_file_exists(compressed_file, global_config['vultr_s3_client']):
                if not await check_redirect_hash(compressed_file, global_config['vultr_s3_client']):
                    await message.edit(content=f"{warning} Your map `{map_name}` differs from the map on the server. Please upload a new version of the map.")
                    return
        except requests.exceptions.Timeout as e:
            await message.edit(content=f"{warning} Cannot check md5 hash, S3 is down. Uploading anyways, this may cause map differs errors...")
            time.sleep(5)
            print(e)
        except Exception as e:
            print(e)
            await message.edit(content=f"{warning} Cannot check md5 hash, S3 is down (something else happened too). Uploading anyways, this may cause map differs errors...")

        # Upload to servers

        try:
            r = requests.get(
                'https://sjc1.vultrobjects.com/tf2maps-maps/maps/1cp_seafoam_a1.bsp.bz2', timeout=4)
            await message.edit(content=f"{loading} Uploading `{filename}` to servers...")
            await asyncio.gather(
                upload_to_redirect(
                    compressed_file, global_config['vultr_s3_client'])
            )
        except requests.exceptions.Timeout as e:
            await message.edit(content=f"{loading} Uploading `{filename}` to servers... except S3.")
            print(e)
        except Exception as e:
            print(e)
            await message.edit(content=f"{loading} Uploading `{filename}` to servers... except S3.")

        await asyncio.gather(
            upload_to_gameserver(
                filepath, **global_config.sftp.us_tf2maps_net),
            upload_to_gameserver(filepath, **global_config.sftp.eu_tf2maps_net)
        )

        # Insert map into DB
        await message.edit(content=f"{loading} Putting `{map_name}` into the map queue...")

        if old_map:
            old_map.url = link
            old_map.map = map_name
            if notes:
                old_map.notes = notes
            await old_map.save()
            await message.edit(content=f"{success} Updated `{map_name}` successfully! Ready for testing!")
        else:
            await Maps.create(
                discord_user_handle=f"{ctx.author.display_name}",
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

        matched_link = None
        if parsed_url.netloc == "tf2maps.net" or parsed_url.netloc == "www.tf2maps.net":
            # Example: https://tf2maps.net/downloads/pullsnake.11004/
            if re.match("^/(downloads|threads)/[\w\-]+\.\d+\/?$", parsed_url.path):
                async with httpx.AsyncClient() as client:
                    response = await client.get(link, follow_redirects=True, timeout=30)
                soup = BeautifulSoup(response.text, 'html.parser')
                href = soup.select(".button--icon--download")[0].get("href")

                # matched_link = f"https://tf2maps.net/{href}"
                matched_link = f"https://tf2maps.net{href}"

            # Example: https://tf2maps.net/downloads/pullsnake.11004/download?version=29169
            elif re.match("^/downloads/\w+\.\d+/download$", parsed_url.path):
                matched_link = link

        async with httpx.AsyncClient() as client:

            if str(link).startswith("https://tf2maps.net"):
                response = await client.head(link, follow_redirects=True, timeout=30)
            # dropbox
            else:
                response = await client.get(link)
            redir = urlparse(str(response.url))

            # Example: https://www.dropbox.com/s/6tyvkwc0af81k9e/pl_cactuscanyon_b1_test.bsp?dl=0
            if redir.netloc == "dropbox.com" or redir.netloc == "www.dropbox.com":

                matched_link = str(response.url).replace("dl=0", "dl=1")

            # Stopped working
            # if redir.netloc == 'cdn.discordapp.com':
            #    if str(link).startswith('https://cdn.discordapp.com/attachments/'):
            #        return link

        return matched_link

        # TODO discord
        # https://cdn.discordapp.com/attachments/556127848998502411/1138620878263963719/cp_fortezza_b1.zip
        # https://cdn.discordapp.com/attachments/1117898068596113428/1138631053137944656/cp_baxter_a3.bsp

        # TODO Direct link
        # Example: http://maps.tf2.games/maps/jump_pyro_b1.bsp

        # TODO Google Drive Link
        # Example: https://drive.google.com/file/d/17KXUZV7iHUL_A5pwOGNbVkbeCXUDIOgo/view?usp=sharing
        #          embeds link in page: https://drive.google.com/u/0/uc?id=17KXUZV7iHUL_A5pwOGNbVkbeCXUDIOgo&export=download

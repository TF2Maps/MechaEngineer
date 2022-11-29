# Std Lib Imports
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
from discord.ext.commands import Cog, command, has_any_role
import discord
import httpx
from tortoise.expressions import Q

#Slash Command Imports
from discord.commands import (
    slash_command,
    Option,
    message_command,
    user_command
)

# Local Imports
from utils import load_config, cog_error_handler, get_srcds_server_info
from utils.emojis import success, warning, error, info, loading
from utils.files import compress_file, download_file, get_download_filename, upload_to_gameserver, upload_to_redirect, remote_file_exists, redirect_file_exists, check_redirect_hash
from utils.search import search_downloads, ForumUserNotFoundException
from utils.discord import not_nobot_role

global_config = load_config()

class MappingHelp(Cog):
    cog_command_error = cog_error_handler

    @discord.slash_command(description="Check forums.", guild_ids=[global_config.guild_id])
    async def forums(self, ctx):
        message = await ctx.respond(f"{loading} Checking...", ephemeral=True)

        #test thread in mapping help
        threads = await ctx.guild.fetch_channel(1022339320037773344)
        print(threads)
        print(await threads.fetch_members())
        print("APPLIED TAGS:")
        print(threads.applied_tags)
        print("FLAGS:")
        print(threads.flags.value)
        print(threads.flags.require_tag)
        
        
        print("")
        print(threads.last_message)
        print(threads.owner)
        print(threads.parent)
        print(threads.type)

    @discord.slash_command(description="Close a thread in mapping-help.", guild_ids=[global_config.guild_id])
    async def close(self, ctx):
        message = await ctx.respond(f"Closing thread!")

        #get thread ID
        channel_id = ctx.channel.id
        print(ctx.channel.id)

        #add tag to channel
        thread = await ctx.guild.fetch_channel(channel_id)
        print(thread.applied_tags)
        await thread.edit(
            name=thread,
            archived=True,
            locked=False,
            invitable=True,
            auto_archive_duration=60,
            slowmode_delay=0,
            reason=f"Marked as solved by {ctx.author}.",
            pinned=False,
            applied_tags=[thread.parent.get_tag(1019705907900334206),]
            )

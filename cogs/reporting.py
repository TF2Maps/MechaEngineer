# Std Lib Imports

# 3rd Party Imports
from discord.ext.commands import Cog, command, has_any_role
import discord

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
#config = global_config.cogs.reporting

class Reporting(Cog):
    cog_command_error = cog_error_handler

    def __init__(self , bot) :
        self.bot = bot

    #report command for menu
    @discord.message_command(name="Report Message", guild_ids=[global_config.guild_id])
    async def report(self, ctx, message: discord.Message):
        await ctx.respond(content=f"{ctx.author.name}, you've reported the message to the staff team for breaking the rules.", ephemeral=True)

        channel = await ctx.guild.fetch_channel(global_config.report_channel_id)

        #build embed to send
        embed = discord.Embed(color=0xff9933)
        embed.set_author(name=f"{message.author.name}#{message.author.discriminator}", icon_url=message.author.avatar)
        embed.add_field(name="Message:", value=message.content, inline=False)
        embed.set_footer(text=global_config.bot_footer)

        await channel.send(content=f"<@{ctx.author.id}> has reported the following message for breaking the rules.", embed=embed)
        await channel.send(content=f"https://discord.com/channels/{global_config.guild_id}/{message.channel.id}/{message.id}")
        
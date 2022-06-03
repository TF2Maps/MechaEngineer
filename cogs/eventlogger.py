# Std Lib Imports
from datetime import datetime

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

global_config = load_config()
#config = global_config.cogs.reporting

class EventLogger(Cog):
    cog_command_error = cog_error_handler

    def __init__(self , bot) :
        self.bot = bot

    @Cog.listener()
    async def on_member_update(self, before, after):

        username = str(after.display_name) + "#" + str(after.discriminator)

        guild = self.bot.get_guild(global_config.guild_id)
        log_channel = await guild.fetch_channel(global_config.modlog_channel_id)

        embed = discord.Embed(
            color=0xff9933
        )
        embed.set_author(name="Audit Log", icon_url=after.display_avatar)
        embed.set_footer(text=global_config.bot_footer)

        #timeout
        if after.timed_out is True:

            embed.add_field(name="Action:", value="Timeout", inline=True)

            #dont ask it works
            datetime_object = after.communication_disabled_until
            dt_until = datetime(datetime_object.year, datetime_object.month, datetime_object.day, datetime_object.hour, datetime_object.minute, datetime_object.second)
            until = dt_until.strftime('%Y-%m-%d %H:%M:%S')

            async for entry in guild.audit_logs(limit=1):

                #dont ask it works
                datetime_object_now = datetime.now()
                dt_now = datetime(datetime_object_now.year, datetime_object_now.month, datetime_object_now.day, datetime_object_now.hour, datetime_object_now.minute, datetime_object_now.second)
                now = dt_now.strftime('%Y-%m-%d %H:%M:%S')

                embed.add_field(name="Issued To:", value=entry.target, inline=False)
                embed.add_field(name="Time:", value=now + " - UTC", inline=False)
                embed.add_field(name="Until:", value=until + " - UTC", inline=False)
                embed.add_field(name="Admin:", value=entry.user, inline=False)

            await log_channel.send(content=f"", embed=embed)

    #on_guild_remove for kicks, bans, 
    #on_member_ban for bans
    #on_member_unban for unbans
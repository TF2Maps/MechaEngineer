# Std Lib Imports
from datetime import datetime

# 3rd Party Imports
from discord.ext.commands import Cog, command, has_any_role
import discord
from steam.steamid import SteamID

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

from models import VerificationDB

global_config = load_config()
#config = global_config.cogs.reporting

class Verification(Cog):
    cog_command_error = cog_error_handler

    def __init__(self , bot) :
        self.bot = bot

    #verify command for menu (not done)
    @discord.message_command(name="Verify User", guild_ids=[global_config.guild_id])
    async def verify(self, ctx, message: discord.Message):
        await ctx.respond(content=f"<@{ctx.author.id}> is verifying <@{message.author.id}>", ephemeral=True)

    #only to be done by mods+
    @discord.slash_command(description="Search the verification database.", guild_ids=[global_config.guild_id])
    async def verify_search(self, ctx, steam_link: discord.Option(str, required=True)):
        steam_id64 = SteamID.from_url(steam_link)

        if(await self.already_verified(steam_id64) == True):
            #this gives us the pkey for the row that the data is in
            they_are_verified = await VerificationDB.filter(verified_steam_id64=steam_id64).all()

            #can get count for this
            db_hits = await VerificationDB.filter(verified_steam_id64=steam_id64).count()
            
            embed = discord.Embed(color=0xff9933)
            embed.set_author(name=f"Search results for: {they_are_verified[0].verified_steam_link}")
            embed.set_footer(text=global_config.bot_footer)

            count = 0
            while count < db_hits:

                embed.add_field(name=f"Record {count}", value=f"DiscordID: {they_are_verified[count].verified_uid}, Username: {they_are_verified[count].verified_username}, Steam Link: {they_are_verified[count].verified_steam_link}, SteamID64: {they_are_verified[count].verified_steam_id64}, Time: {they_are_verified[count].time_verified}", inline=False)

                count = count + 1

            await ctx.respond(embed=embed)
        else:
            await ctx.respond(content=f"The steam account has not been used before.")

    #only to be done by mods+
    @discord.slash_command(description="Verify a user.", guild_ids=[global_config.guild_id])
    async def verify(self, ctx, discord_user: discord.User, steam_link: discord.Option(str, required=True), override: discord.Option(bool, required=False)):
        
        #set some variables (makes it cleaner imo)
        verified_role = discord.utils.get(ctx.guild.roles, name="Verified")
        verifier_username = ctx.author # verifier username
        verifier_id = ctx.author.id # verifier id
        verified_username = discord_user # verified username
        verified_id = discord_user.id # verified id
        steam_link = steam_link # steam link
        overridden = False
        #bot will error out of garbage is entered
        steam_id64 = SteamID.from_url(steam_link)  # steam id - works with either custom url or standard links
        
        await ctx.respond(content=f"Checking if steam account has already been verified.", ephemeral=True)

        #check if previously used
        if(await self.already_verified(steam_id64) == True):

            #check if the override was set
            if(override == True):
                overridden = True
                await ctx.edit(content=f"Steam account has been previously been used! Overriding!")
                await self.verify_user(ctx, verifier_username, verifier_id, verified_username, verified_id, steam_link, steam_id64, overridden)
                await discord_user.add_roles(verified_role)

            else:
                await ctx.edit(content=f"Steam account has been previously been used! If you want to override, set the optional parmaeter!")

        else:
            await ctx.edit(content=f"Steam account has not previously been used.")
            await self.verify_user(ctx, verifier_username, verifier_id, verified_username, verified_id, steam_link, steam_id64, overridden)
            await discord_user.add_roles(verified_role)

    #we check the database
    async def already_verified(self, steam_id64):
        they_are_verified = await VerificationDB.filter(verified_steam_id64=steam_id64).all()
        if len(they_are_verified) > 0:
            return True
        else:
            return False

    #we do database stuff
    async def verify_user(self, ctx, verifier_username, verifier_id, verified_username, verified_id, steam_link, steam_id64, overridden):
        await VerificationDB.create(
            verifier_uid=verifier_id,
            verifier_username=verifier_username,
            verified_uid=verified_id,
            verified_username=verified_username,
            verified_steam_link=steam_link,
            verified_steam_id64=steam_id64,
            time_verified=datetime.now(),
            overridden=overridden
        )
        await ctx.edit(content=f"{success} Verified <@{verified_id}>.")

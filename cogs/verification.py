# Std Lib Imports

# 3rd Party Imports
import discord
from discord.ext.commands import Cog, slash_command, user_command

# Local Imports
from utils import load_config, cog_error_handler
from utils.emojis import github
from utils.discord import not_nobot_role_slash, roles_required

global_config = load_config()
config = global_config.cogs.verification


class Verification(Cog):
    cog_command_error = cog_error_handler

    @user_command(
        name="verify", 
        description=config.verify.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.verify.role_names),
            not_nobot_role_slash()
        ]
    )
    async def verify(self, ctx, member: discord.Member):
        unverified_role = discord.utils.get(ctx.guild.roles, name="Unverified")
        verified_role = discord.utils.get(ctx.guild.roles, name="Verified")

        #for if they have both! take away unverified.
        if unverified_role in member.roles and verified_role in member.roles:
            await member.remove_roles(unverified_role)
            await ctx.respond(f"{member.name} has both Unverified and Verified. Removing Unverified.", ephemeral=True)
            return
        
        #check if they have a verified role already
        if verified_role in member.roles and unverified_role not in member.roles:
            await ctx.respond(f"{member.name} is already Verified!", ephemeral=True)
            return

        if unverified_role in member.roles:
            await member.remove_roles(unverified_role)
        await member.add_roles(verified_role)
        await ctx.respond(f"{member.name} is Verified now.", ephemeral=True)
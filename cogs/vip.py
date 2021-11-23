# Std Lib Imports
pass

# 3rd Party Imports
import discord
from discord.ext.commands import Cog, command, has_any_role
import databases

# Local Imports
from utils import load_config, cog_error_handler
from utils.emojis import success, warning, error, info, loading
from utils.discord import not_nobot_role


global_config = load_config()
config = global_config.cogs.vip

class VIP(Cog):
    cog_command_error = cog_error_handler

    #check if vip is still valid
	#this is probably going to need to be threaded?
    @Cog.listener()
    async def on_message(self, message):

        #vip role
        vip_role = discord.utils.get(message.guild.roles, name="VIP")

        #stop bot from replying to itself :)
        if message.author.bot:
            return
		
        #don't bother checking if they are still a vip if they don't have the role in the first place...
        if vip_role in message.author.roles:

            #connect to xf database
            database = databases.Database(global_config.databases.tf2maps_site)
            await database.connect()

            #check if discord id is linked
            query = "SELECT user_id FROM xf_user_field_value WHERE field_id = :field_id AND field_value = :field_value"
            values = {"field_id": "discord_user_id", "field_value": message.author.id}
            result = await database.fetch_one(query=query, values=values)

            #if their discord account isn't linked but they have vip, remove it to be safe.
            if result is None:
                await message.channel.send("<@" + str(message.author.id) + "> You don't have your discord account linked on the forums yet you have vip. Upgrade to VIP https://tf2maps.net/account/upgrades")
                await message.author.remove_roles(vip_role)
                return

            #check if they are vip
            query = "SELECT secondary_group_ids FROM xf_user WHERE user_id = :user_id AND find_in_set(:vip_gid, secondary_group_ids)"
            values = {"user_id": result[0], "vip_gid": 19}
            result = await database.fetch_one(query=query, values=values)
            #if not remove vip role otherwise do nothing :)
            if not result:
                await message.channel.send("<@" + str(message.author.id) + "> Your VIP status has expired. Upgrade to VIP https://tf2maps.net/account/upgrades")
                await message.author.remove_roles(vip_role)
                return

    @command(aliases=config.upgrade.aliases, help=config.upgrade.help)
    @has_any_role(*config.upgrade.role_names)
    @not_nobot_role()
    async def upgrade(self, ctx):
        database = databases.Database(global_config.databases.tf2maps_site)
        await database.connect()

        query = "SELECT user_id FROM xf_user_field_value WHERE field_id = :field_id AND field_value = :field_value"
        values = {"field_id": "discord_user_id", "field_value": ctx.author.id}
        result = await database.fetch_one(query=query, values=values)

        if not result:
            await ctx.reply(f"{error} You don't seem to have a Discord User ID # set in your TF2Maps.net profile.\nSee here on how to get started: http://bot.tf2maps.net/faq.php'")
            return

        query = "SELECT secondary_group_ids FROM xf_user WHERE user_id = :user_id AND find_in_set(:vip_gid, secondary_group_ids)"
        values = {"user_id": result[0], "vip_gid": 19}
        result = await database.fetch_one(query=query, values=values)

        if not result:
            await ctx.reply(f"{error} You must be a VIP user on TF2Maps.net for the discord VIP Role.")
            return

        vip_role = discord.utils.get(ctx.guild.roles, name="VIP")

        if vip_role in ctx.author.roles:
            await ctx.send(f"{warning} You're already a VIP, go away.")
            return

        await ctx.author.add_roles(vip_role)
        await ctx.reply(f"{info} You are now a :star2: TF2Maps Discord VIP :star2: ")

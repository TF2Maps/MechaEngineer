# Std Lib Imports
import requests
import urllib.request
import json
import time
import datetime
import ast

# 3rd Party Imports
import discord
from discord.ext.commands import Cog, slash_command
import databases
from rcon.source import rcon
from steam.steamid import SteamID

# Local Imports
from utils import load_config, cog_error_handler
from utils.discord import not_nobot_role_slash, roles_required
from utils.emojis import success, warning, error, info, loading

global_config = load_config()
config = global_config.cogs.hosts
sftp_config = global_config.sftp

class Hosts(Cog):
    cog_command_error = cog_error_handler


    @slash_command(
        name="addhost", 
        description=config.addhost.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.addhost.role_names),
            not_nobot_role_slash()
        ]
    )
    async def addhost(self, ctx, user: discord.Option(discord.Member, description="discord user")):
       
        await ctx.respond(f"{loading} Adding {user.name} to hosts group...")
        time.sleep(2)
        database = databases.Database(global_config.databases.tf2maps_site)
        await database.connect()
        
        #get their forum ID
        query = "SELECT user_id FROM xf_user_connected_account WHERE provider_key = :field_value"
        values = {"field_value": user.id}
        result = await database.fetch_one(query=query, values=values)

        #has connected discord account check
        if not result:
            await ctx.edit(content=f"{error} {user.name} doesn't have a Discord User ID # set in their TF2Maps.net profile.\nSee [this help page](<http://bot.tf2maps.net/faq.php>) on how to get started.")
            return

        user_id = result[0]
        user_secondary_groups = await self.get_user_roles(user_id)

        if 41 in user_secondary_groups:
            await ctx.edit(content=f"{warning} {user.name} already has the hosts group on the forum! Checking discord...")
            time.sleep(3)
        else:
            message = await ctx.edit(content=f"{loading} Adding {user.name} to hosts group on the forums...")
            time.sleep(2)
            await self.add_user_hosts(ctx, message, user_id, user_secondary_groups, user)
        

        message = await ctx.edit(content=f"{loading} Adding {user.name} to hosts group on discord...")
        time.sleep(2)
        ##discord role stuff
        host_role = discord.utils.get(ctx.guild.roles, name="Hosts")
        if host_role in ctx.user.roles:
            await ctx.edit(content=f"{warning} They're already a Host, go away.")
            return
        await user.add_roles(host_role)
        await ctx.edit(content=f"{success} Added {user.name} to the Hosts group on discord.")

    @slash_command(
        name="delhost", 
        description=config.delhost.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.delhost.role_names),
            not_nobot_role_slash()
        ]
    )
    async def delhost(self, ctx, user: discord.Option(discord.Member, description="discord user")):
        await ctx.respond(f"{loading} Removing {user.name} from hosts group...")
        time.sleep(2)
        database = databases.Database(global_config.databases.tf2maps_site)
        await database.connect()
        
        #get their forum ID
        query = "SELECT user_id FROM xf_user_connected_account WHERE provider_key = :field_value"
        values = {"field_value": user.id}
        result = await database.fetch_one(query=query, values=values)

        #has connected discord account check
        if not result:
            await ctx.edit(content=f"{error} {user.name} doesn't have a Discord User ID # set in their TF2Maps.net profile.\nSee [this help page](<http://bot.tf2maps.net/faq.php>) on how to get started.")
            return

        user_id = result[0]
        user_secondary_groups = await self.get_user_roles(user_id)
        print(user_secondary_groups)

        if 41 not in user_secondary_groups:
            await ctx.edit(content=f"{warning} {user.name} is already removed from the xenforo group! Checking discord...")
            time.sleep(3)
        else:
            
            message = await ctx.edit(content=f"{loading} Removing {user.name} from hosts group on the forums...")
            time.sleep(2)
            #await self.add_user_hosts(ctx, message, user_id, user_secondary_groups, user)
            await self.del_user_hosts(ctx, message, user_id, user_secondary_groups, user)

        
        message = await ctx.edit(content=f"{loading} Removing {user.name} from hosts group on discord...")
        time.sleep(2)
        ###discord role stuff
        host_role = discord.utils.get(ctx.guild.roles, name="Hosts")
        if host_role not in ctx.user.roles:
            await ctx.edit(content=f"{warning} They're not a Host already, go away.")
            return
        await user.remove_roles(host_role)
        await ctx.edit(content=f"{success} Removed {user.name} from the Hosts group on discord.")

    @slash_command(
        name="temphost", 
        description=config.temphost.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.temphost.role_names),
            not_nobot_role_slash()
        ]
    )
    async def temphost(self, ctx):

        #check if vip first
        vip_role = discord.utils.get(ctx.guild.roles, name="VIP")

        if vip_role not in ctx.author.roles:
            await ctx.respond(f"{warning} You're not a vip, only vip's may get temp-hosting powers for gamedays.")
            return
        
        #check if host already
        hosts_role = discord.utils.get(ctx.guild.roles, name="Hosts")

        if hosts_role in ctx.author.roles:
            await ctx.respond(f"{warning} You're a host already. Go away.")
            return


        #
        # check if user has forum account
        #
        database = databases.Database(global_config.databases.tf2maps_site)
        await database.connect()
        
        #get their forum ID
        query = "SELECT user_id FROM xf_user_connected_account WHERE provider_key = :field_value"
        values = {"field_value": ctx.author.id}
        result = await database.fetch_one(query=query, values=values)

        #has connected discord account check
        if not result:
            await ctx.edit(content=f"{error} You don't have a Discord User ID # set in your TF2Maps.net profile.\nSee [this help page](<http://bot.tf2maps.net/faq>) on how to get started.")
            return
        
        user_forum_id = result[0]

        #check if server has a lot of people on it
            #how to know what server they are on
                #rcon
            #is that worth the effort?

        query = "SELECT provider_key FROM xf_user_connected_account WHERE provider = 'th_cap_steam' AND user_id = :user_id"
        values = {"user_id": user_forum_id}
        result = await database.fetch_one(query=query, values=values)
        if result is None:
            await ctx.respond(f"{error} You do not have a steam account linked.")
            return
        user_steam_id = result[0].decode("utf-8")

        user_steam3 = SteamID(user_steam_id).as_steam3

        on_server = False

        response_us = await rcon('api_steamids', host="us.tf2maps.net", port=27015, passwd=sftp_config.us_tf2maps_net.rcon)
        players_us = ast.literal_eval(response_us)

        #loop through api for player steamid
        for player in players_us:
            steam_id = player['steam_id']
            if steam_id == user_steam3:
                if len(players_us) > 16:
                    await ctx.respond(f"{warning} There is more than 16 players on the US server. We are assuming there is a map test on-going.")
                    return
                on_server = True
                break

        response_eu = await rcon('api_steamids', host="eu.tf2maps.net", port=27015, passwd=sftp_config.eu_tf2maps_net.rcon)
        players_eu = ast.literal_eval(response_eu)

        #loop through api for player steamid
        for player in players_eu:
            steam_id = player['steam_id']
            if steam_id == user_steam3:
                if len(players_us) > 16:
                    await ctx.respond(f"{warning} There is more than 16 players on the EU server. We are assuming there is a map test on-going.")
                    return
                on_server = True
                break

        if on_server is False:
            await ctx.respond(f"{error} You are not present on the server or you haven't linked your accounts to the forums.")
            return

        #grant temp host
        await ctx.respond(f"{loading} Adding you to the temp-hosts forum group...")
        time.sleep(2)

        #add to role
        user_secondary_groups = await self.get_user_roles(user_forum_id)

        if 43 in user_secondary_groups:
            await ctx.edit(content=f"{warning} {ctx.author.name} already has the temp-hosts group on the forum!")
            time.sleep(3)
        else:
            message = await ctx.edit(content=f"{loading} Adding {ctx.author.name} to temp-hosts group on the forums...")
            time.sleep(2)
            await self.add_user_temp_host(ctx, message, user_forum_id, user_secondary_groups, ctx.author)

        pass

    async def get_user_roles(self, user_id):
        #
        # Send API request for user groups
        #
        headers = {
                'Content-type' : 'application/x-www-form-urlencoded',
                'XF-Api-Key' : global_config.apikeys.xenforo.key
                }
        
        params = {
            'api_bypass_permissions': 1
        }
        url = f'https://tf2maps.net/api/users/{user_id}/'
        r = requests.get(url, headers=headers, params=params)

        jsonR = r.json()
        user_secondary_groups = jsonR['user']['secondary_group_ids']    

        return user_secondary_groups
    
    #add user to XF group via api
    async def add_user_hosts(self, ctx, message, user_id, user_secondary_groups, user):
        #
        # API POST for adding user group
        #
        #have to pass more than one group
        #otherwise it wipes all secondary groups
        #set group 2 which is registeded
        #if the primary group is that it wont
        #override and will not add it to secondary
        #while still adding the other groups
        user_secondary_groups.extend([2, 41,])
        
        headers = {
            'Content-type' : 'application/x-www-form-urlencoded',
            'XF-Api-Key' : global_config.apikeys.xenforo.key
        }
        params = {
            'api_bypass_permissions': 1
        }
        data = {
            'secondary_group_ids[]': [user_secondary_groups],
        }

        url = f'https://tf2maps.net/api/users/{user_id}/'
        r = requests.post(url, headers=headers, params=params, data=data)

        if r.status_code == 200:
            await ctx.edit(content=f"{success} Added {user.name} to the hosts group on the forums.")
            time.sleep(2)
            return
        
        await ctx.edit(content=f"{error} Unable to add {user.name} to the hosts group on the forums.")
        return
    
    #remove user from XF group via api
    async def del_user_hosts(self, ctx, message, user_id, user_secondary_groups, user):

        user_secondary_groups.remove(41)

        headers = {
            'Content-type' : 'application/x-www-form-urlencoded',
            'XF-Api-Key' : global_config.apikeys.xenforo.key
        }
        params = {
            'api_bypass_permissions': 1
        }
        data = {
            'secondary_group_ids[]': [user_secondary_groups],
        }

        url = f'https://tf2maps.net/api/users/{user_id}/'
        r = requests.post(url, headers=headers, params=params, data=data)

        if r.status_code == 200:
            await ctx.edit(content=f"{success} Removed {user.name} from the hosts group on the forums.")
            time.sleep(2)
            return
        
        await ctx.edit(content=f"{error} Unable to remove {user.name} from the hosts group on the forums.")
        return
    
    #for temp-host gameday role
    async def add_user_temp_host(self, ctx, message, user_id, user_secondary_groups, user):
        user_secondary_groups.extend([2, 43,])
        
        headers = {
            'Content-type' : 'application/x-www-form-urlencoded',
            'XF-Api-Key' : global_config.apikeys.xenforo.key
        }
        params = {
            'api_bypass_permissions': 1
        }
        data = {
            'secondary_group_ids[]': [user_secondary_groups],
        }

        url = f'https://tf2maps.net/api/users/{user_id}/'
        r = requests.post(url, headers=headers, params=params, data=data)

        if r.status_code == 200:
            await ctx.edit(content=f"{success} Added {user.name} to the temp-hosts group on the forums.")
            time.sleep(2)
            return
        
        await ctx.edit(content=f"{error} Unable to add {user.name} to the temp-hosts group on the forums.")
        return

    async def del_user_hosts(self, ctx, message, user_id, user_secondary_groups, user):
        pass
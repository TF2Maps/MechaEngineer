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
    async def temphost(self, ctx, user: discord.Option(discord.Member, description="discord user")):
     
        #check if host already
        hosts_role = discord.utils.get(ctx.guild.roles, name="Hosts")

        if hosts_role in ctx.author.roles:
            await ctx.respond(f"{warning} They're a host already. Go away.")
            return
        
        #check if temp-host already
        temphosts_role = discord.utils.get(ctx.guild.roles, name="Temp-Host")

        if temphosts_role in ctx.author.roles:
            await ctx.respond(f"{warning} They're a temp-host already. Go away.")
            return

        #do site things
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

        if 43 in user_secondary_groups:
            await ctx.edit(content=f"{warning} {user.name} already has the temp-host group on the forum! Checking discord...")
            time.sleep(3)
        else:
            message = await ctx.edit(content=f"{loading} Adding {user.name} to temp-host group on the forums...")
            time.sleep(2)
            await self.add_user_hosts(ctx, message, user_id, user_secondary_groups, user)
        

        message = await ctx.edit(content=f"{loading} Adding {user.name} to hosts group on discord...")
        time.sleep(2)
        ##discord role stuff
        temphost_role = discord.utils.get(ctx.guild.roles, name="Temp-Host")
        if temphost_role in ctx.user.roles:
            await ctx.edit(content=f"{warning} They're already a Host, go away.")
            return
        await user.add_roles(temphosts_role)
        await ctx.edit(content=f"{success} Added {user.name} to the Temp-Host group on discord.")
        
    @slash_command(
        name="listtemphosts", 
        description=config.listtemphosts.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.listtemphosts.role_names),
            not_nobot_role_slash()
        ]
    )
    async def listtemphosts(self, ctx):

        temphost_role = discord.utils.get(ctx.guild.roles, name="Temp-Host")
        if len(temphost_role.members) == 0:
            await ctx.respond("No one has the Temp-Host role.")
            return

        output_list = ""
        for member in temphost_role.members:
            output_list = output_list + str(member.name) + "\n"
        await ctx.respond("Here is the list of users who have the temp-host role: ```" + output_list + "```If there are no gamedays, no one should have this role.")
        return


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

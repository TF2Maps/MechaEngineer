#un implemented.

import discord
from discord.ext.commands import Cog, command, has_any_role
from utils import load_config
import a2s
import re
from rcon import Client
from utils import load_config, cog_error_handler
from utils.discord import not_nobot_role
#https://pypi.org/project/rcon/



global_config = load_config()
config = global_config

class Rcon(Cog):

    cog_command_error = cog_error_handler

    #sm_say works but returns an error message in vsc because there is no return message to discord.
    @command(help=config.cogs.rcon.rcon.help)
    @has_any_role(*config.cogs.servercontrol.server.role_names)
    async def rcon(self, ctx, server, *commands):

        #what servers can we rcon
        servers = ["eu", "us", "eumvm", "usmvm"]

        #only accept valid servers
        if server in servers:

            command = " ".join(commands)
            response = await run_rcon(server, command)

            #for status, this is important!!!!
            if command == "status":
                status_response = await get_status(response)
                await ctx.send(status_response)
            else:
            #for everything else
                if response == "":
                    await ctx.send("Command sent.")
                else:
                    await ctx.send("```\n" + response + "\n```")
            
        #wrong server
        else:
            await ctx.send("Invalid server. See `!server`.")

    #nextmap
    @command(help=config.cogs.rcon.nextmap.help)
    @has_any_role(*config.cogs.rcon.nextmap.role_names)
    async def nextmap(self, ctx, server):
        await ctx.trigger_typing()
        if server == "us":

            nextmap = get_nextmap('us.tf2maps.net', 27015)
            await ctx.send(nextmap)

        elif server == "us-mvm":

            nextmap = get_nextmap('us.tf2maps.net', 27016)
            await ctx.send(nextmap)

        elif server == "eu":

            nextmap = get_nextmap('eu.tf2maps.net', 27015)
            await ctx.send(nextmap)

        elif server == "eu-mvm":

            nextmap = get_nextmap('eu.tf2maps.net', 27016)
            await ctx.send(nextmap)
        
        else:
            await ctx.send("no server found")

#get the next fucking map
def get_nextmap(host, port):
    rules = str(a2s.rules((host, port)))
    
    #turns a2s.rules into list
    dalist = rules.split(',')

    #jank ass code that grabs the sm_nextmap part of that sea of words
    splitter = []
    for x in dalist:
        if "sm_nextmap" in x:
            splitter.append(x)

    #wish I didn't have to do this
    almostthere = splitter[0]
    #split the new list and grab the second half
    nextmap = almostthere.split(':', 1)
    #remove the dumb '
    thenextmap = re.sub("'", ' ', nextmap[1])
    
    return thenextmap

async def get_status(input):

    #things we need to grab from status
    #userid 1
    #name 2
    #uniqueid 3
    #adr 8

    #status header
    header = input.split('#')[1]
    print(header)
    print("header")
    
    nospaceheader = re.sub(' +', ' ', header)
    print(nospaceheader)

    headersplit = nospaceheader.split(' ')
    del headersplit[0]
    headersplit.remove('connected')
    headersplit.remove('ping')
    headersplit.remove('loss')
    headersplit.remove('state')

    print(headersplit)

    #drops top section before names on status
    status = "```\n" + input.split('#', 1)[1] + "\n```"

    #no excess spaces
    nospacestatus = re.sub(' +', ' ', status)
    print(nospacestatus)


    splitboy = input.split('#', 2)[2]
    nospace = re.sub(' +', ' ', splitboy)
    print(str(nospace))

    return status

async def run_rcon(server, command):

    if server == "eu":
        with Client(config.rcon.euip, port=config.rcon.imp, passwd=config.rcon.password) as client:
                        rcon_output = client.run(command)
    elif server == "us":
        with Client(config.rcon.usip, port=config.rcon.imp, passwd=config.rcon.password) as client:
                        rcon_output = client.run(command)
    elif server == "eumvm":
        with Client(config.rcon.euip, port=config.rcon.mvm, passwd=config.rcon.password) as client:
                        rcon_output = client.run(command)
    elif server == "usmvm":
        with Client(config.rcon.us, port=config.rcon.mvm, passwd=config.rcon.password) as client:
                        rcon_output = client.run(command)                 
    else:
        rcon_output = "Oops you haven't written this part yet."

    #raw unfiltered output
    return rcon_output
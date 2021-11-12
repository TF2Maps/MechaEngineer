import asyncio
import socket
import discord
from discord.ext.commands import Cog, command, has_any_role
from utils import load_config, cog_error_handler
from utils.discord import not_nobot_role
import asyncssh

global_config = load_config()
config = global_config

class Server(Cog):

    cog_command_error = cog_error_handler

    #server command: start, stop, restart, update
    @command(help=config.cogs.servercontrol.server.help)
    @has_any_role(*config.cogs.servercontrol.server.role_names)
    async def server(self, ctx, server, command):

        servers = ["eu", "us", "eumvm", "usmvm"]
        commands = ["start", "stop", "restart", "update", "ping"]

        if command in commands:
            if server in servers:
                #eu
                if server == "eu":
                    await ctx.send(await server_connection("tf", "eu.tf2maps.net", 27015, command))
                #us
                elif server == "us":
                    await ctx.send(await server_connection("tf", "us.tf2maps.net", 27015, command))

                #eumvm
                elif server == "eumvm":
                    await ctx.send(await server_connection("mvm", "eu.tf2maps.net", 27016, command))

                #usmvm
                elif server == "usmvm":
                    await ctx.send(await server_connection("mvm", "us.tf2maps.net", 27016, command))

                else:
                    await ctx.send("How did it reach this part?")

            else:
                await ctx.trigger_typing()
                await ctx.send("Server not found.")

        else:
            await ctx.send("Invalid command argument.")

#server connecting
async def server_connection(user, hostname, port, command):

    commands = ["start", "stop", "restart", "update", "ping"]

    async with asyncssh.connect(
        hostname,
        port=22, 
        username=user, 
        password=config.sftp.master.password,
        known_hosts=None
    ) as conn:
        if command in commands:
            if command == "start":

                await conn.run('./server start')

                #check if server is up
                await asyncio.sleep(8)
                if await check_port(hostname, port):
                    return "Server started."
                else:
                    return "Server not started."

            elif command == "stop":

                await conn.run('./server stop')

                #check if server is running
                await asyncio.sleep(5)
                if await check_port(hostname, port):
                    return "Server not stopped."
                else:
                    return "Server is stopped."
 
            elif command == "restart":

                #stop server and update
                await conn.run('./server stop') 
                await asyncio.sleep(5)
                await conn.run('./server update')

                #check if server is up
                await asyncio.sleep(8)
                if await check_port(hostname, port):
                    return "Server restarted."
                else:
                    return "Server not restarted."

            elif command == "update":
                
                await conn.run('./server update')

                #check if server is up
                await asyncio.sleep(10)
                if await check_port(hostname, port):
                    return "Server online and updated."
                else:
                    return "Server offline."

            elif command == "ping":
                if await check_port(hostname, port):
                    return "Server online."
                else:
                    return "Server offline."

            else:
                return "How did you manage to break this after a checksum?" 

        else:
            return "Invalid command."

#semi dirty way to check if the server is up
async def check_port(hostname, port):
    a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    location = (hostname, port)

    result_of_check = a_socket.connect_ex(location)

    if result_of_check == 0:
        return True
    else:
        return False
    pass
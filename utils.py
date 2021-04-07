import discord
import yaml
from dotted_dict import DottedDict


def load_config():
    with open("config.yaml") as file:
        config = yaml.load(file)
    return DottedDict(config)

async def connect_db(database):
    # This should be done using normal SQLAlchemy semantics;
    # The box this is on has a broken dep chain which prevents using create_engine
    if not database.is_connected:
        await database.connect()

def error(message):
    return discord.Embed(title='<:error:828978696957198357> Error', description=message)

def warning(message):
    return discord.Embed(title='<:warning:828978696680898601> Warning', description=message)

def info(message):
    return discord.Embed(title='<:info:828978697003728896> Info', description=message)

def success(message):
    return discord.Embed(title='<:success:828981169861165066> Success', description=message)

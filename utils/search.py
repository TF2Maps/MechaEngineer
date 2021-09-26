# Std Lib Imports
import re

# 3rd Party Imports
import discord
from bs4 import BeautifulSoup
import httpx
import databases
from dotted_dict import DottedDict
import a2s

# Local Imports
from .config import load_config
global_config = load_config()

class ForumUserNotFoundException(Exception):
    pass


async def search_downloads(resource_name, discord_user_id=None):
    database = databases.Database(global_config.databases.tf2maps_site)
    await database.connect()

    results = []
    if discord_user_id:
        query = "SELECT user_id FROM xf_user_field_value WHERE field_id = :field_id AND field_value = :field_value"
        values = {"field_id": "discord_user_id", "field_value": discord_user_id}
        result = await database.fetch_one(query=query, values=values)
        if not result:
            raise ForumUserNotFoundException

        forum_user_id = result[0]
        query = 'SELECT title,resource_id from xf_resource where user_id=:field_user_id AND title LIKE :field_title'
        values = {"field_user_id": forum_user_id, "field_title": f"%{resource_name}%"}
        results = await database.fetch_all(query=query, values=values)

    else:
        query = 'SELECT title,resource_id from xf_resource where title LIKE :field_title ORDER BY resource_id DESC'
        values = {"field_title": f"%{resource_name}%"}
        results = await database.fetch_all(query=query, values=values)

    links = []
    for name, map_id in results:
        name = re.sub("[^A-z0-9_]", "-", name)
        name = re.sub("-+$", "", name)
        name = re.sub("-{2,}", "-", name)
        name = name.lower()

        links.append(f"https://tf2maps.net/downloads/{name}.{map_id}/")

    return links


async def search_with_bing(site, term, exclude=[]):
    plus_term = "%20".join(term.split(" "))
    exclude_sites = "%20".join([f"-site%3A{site}" for site in exclude])
    search_query = f"https://www.bing.com/search?q=site%3A{site}%20{exclude_sites}%20{plus_term}"

    async with httpx.AsyncClient() as client:
        response = await client.get(search_query)

    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.select("ol#b_results > li.b_algo > h2 > a")

    return [link['href'] for link in links]


def get_srcds_server_info(host, port=27015):
    return a2s.info((host, port))

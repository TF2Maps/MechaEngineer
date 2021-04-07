# Std Lib Imports
pass

# 3rd Party Imports
import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import httpx

# Local Imports
from utils import load_config

global_config = load_config()
config = global_config.cogs.search


class Search(commands.Cog):
    @commands.group(invoke_without_command=True, aliases=config.vdc.aliases, help=config.vdc.help)
    @commands.has_any_role(*config.vdc.role_names)
    async def vdc(self, ctx, *, term):
        embed = await self.search_site("developer.valvesoftware.com/wiki", term, "Valve Developer Wiki", "https://cdn.discordapp.com/attachments/557661188033478656/829218372398481438/vdc_64.png")
        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True, aliases=config.tf2m.aliases, help=config.tf2m.help)
    @commands.has_any_role(*config.tf2m.role_names)
    async def tf2m(self, ctx, *, term):
        embed = await self.search_site("tf2maps.net", term, "TF2 Maps", "https://cdn.discordapp.com/attachments/557661188033478656/829216388757323776/tf2m_64.png")
        await ctx.send(embed=embed)

    @staticmethod
    async def search_site(site, term, title, icon):
        plus_term = "+".join(term.split(" "))

        async with httpx.AsyncClient() as client:
            response = await client.get(f'https://www.bing.com/search?q=site%3A{site}+{plus_term}')

        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.select("ol#b_results > li.b_algo > h2 > a")

        output = f"Showing top **{len(links)}** results for `{term}`\n"
        for link in links:
            # Sometimes it scrapes blank data?
            if not link.text:
                continue

            text = link.text.replace("| TF2Maps.net", "")
            text = link.text.replace("- Valve Developer Community", "")

            output += f"\n• [{text}]({link.get('href')})"

        embed = discord.Embed(
            description=output,
        )
        embed.set_author(name=f"{title} Search", url=f"https://www.bing.com/search?q=site%3A{site}+{plus_term}", icon_url=icon)
        embed.set_footer(text="Powered by Bing")

        return embed
import json

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

import uvicorn

import discord

from utils import load_config
config = load_config()

templates = Jinja2Templates(directory="web")
app = FastAPI()

@app.get("/commands")
async def commands(request: Request):
    return templates.TemplateResponse(
        "commands.html",
        {"request": request, "categories": config.cogs}
    )

@app.post("/alerts")
async def commands(request: Request):
    body = await request.json()
    print(body)
    description = f"{body['message']}\n\u200b"

    url = body['ruleUrl'].replace(":3000", "")

    labels = body['evalMatches'][0]['tags']

    embed = discord.Embed(description=description)
    embed.set_author(name="Grafana Alert", url=url, icon_url=config.icons.grafana_icon)

    if labels:
        embed.add_field(name="Tags", value=f"```{json.dumps(labels, indent=4)}```", inline=True)

    image_url = body.get('imageUrl')
    if image_url:
        embed.set_image(url=image_url)

    client = discord.Client()
    await client.login(config.bot_token, bot=True)
    channel = await client.fetch_channel(818508340019724299)

    await channel.send(embed=embed)


@app.post("/github")
async def github(request: Request):
    body = await request.json()
    event = request.headers.get("X-Github-Event")

    if not event == "push":
        return

    name = body['sender']['login']
    repo = body['repository']['full_name']
    repo_link = body['repository']['html_url']

    description = ""
    for commit in body['commits']:
        commit_hash = commit['id'][:7]
        commit_link = commit['url']
        commit_message = commit['message']
        description += f"[`{commit_hash}`]({commit_link}) - {commit_message}\n"

    embed = discord.Embed(description=description)
    embed.set_author(name="Commits Pushed", icon_url=config.icons.github_icon)
    embed.add_field(name="Repo", value=f"[{repo}]({repo_link})", inline=True)
    embed.add_field(name="Author", value=name, inline=True)

    client = discord.Client()
    await client.login(config.bot_token, bot=True)
    channel = await client.fetch_channel(557661188033478656)

    await channel.send(embed=embed)

    # await client.logout()

@app.get("/")
async def commands(request: Request):
    return templates.TemplateResponse(
        "commands.html",
        {"request": request, "categories": config.cogs}
    )

uvicorn.run(app, host="0.0.0.0", port=8181)

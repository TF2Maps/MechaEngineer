from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

import uvicorn

from utils import load_config
config = load_config()

templates = Jinja2Templates(directory="web")
app = FastAPI()

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        "commands.html",
        {"request": request, "categories": config.cogs}
    )

uvicorn.run(app, host="0.0.0.0", port=8181)

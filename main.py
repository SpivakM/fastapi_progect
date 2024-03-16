from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from api import api_router_user, api_router_auth, general_routers
from web import web_router

app = FastAPI()

app.include_router(api_router_user.router)
app.include_router(api_router_auth.public_router)
app.include_router(general_routers.router_public)
app.include_router(general_routers.router_private)

app.include_router(web_router.web_router)

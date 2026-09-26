from fastapi import FastAPI
from backend.app.api.v1.router import api_router
from backend.app.config import  get_settings
settings = get_settings()
app=FastAPI(title=settings.APP_NAME)

app.include_router(api_router)


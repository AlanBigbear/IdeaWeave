from fastapi import APIRouter

from app.api.v1 import auth, calendar, ideas, inspirations, personas, scripts, settings, topics

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(personas.router)
api_router.include_router(settings.router)
api_router.include_router(inspirations.router)
api_router.include_router(topics.router)
api_router.include_router(ideas.router)
api_router.include_router(scripts.router)
api_router.include_router(calendar.router)

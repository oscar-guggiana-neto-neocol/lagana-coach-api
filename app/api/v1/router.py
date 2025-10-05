from fastapi import APIRouter

from app.api.v1.routers import auth, coaches, players, clubs, strokes, lessons, invoices

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(coaches.router)
api_router.include_router(players.router)
api_router.include_router(clubs.router)
api_router.include_router(strokes.router)
api_router.include_router(lessons.router)
api_router.include_router(invoices.router)

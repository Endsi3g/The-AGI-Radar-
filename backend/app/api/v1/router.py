from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.leads import router as leads_router
from app.api.v1.scrape import router as scrape_router
from app.api.v1.messages import router as messages_router
from app.api.v1.ai import router as ai_router
from app.api.v1.comms import router as comms_router
from app.api.v1.google import router as google_router
from app.api.v1.map import router as map_router

# Placeholder routers for future phases — avoids import errors at boot
from fastapi import APIRouter as _R

campaigns_router = _R(prefix="/campaigns", tags=["campaigns"])

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth_router)
v1_router.include_router(users_router)
v1_router.include_router(leads_router)
v1_router.include_router(scrape_router)
v1_router.include_router(messages_router)
v1_router.include_router(campaigns_router)
v1_router.include_router(ai_router)
v1_router.include_router(google_router)
v1_router.include_router(comms_router)
v1_router.include_router(map_router)

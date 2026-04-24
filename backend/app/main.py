from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging import setup_logging, logger
from app.api.v1.router import v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("HGI Radar starting", env=settings.app_env)
    yield
    logger.info("HGI Radar shutting down")


app = FastAPI(
    title="HGI Radar — Prospecting API",
    version="1.0.0",
    description="Système de prospection complet pour agences numériques québécoises",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)


@app.get("/api/v1/health", tags=["health"])
async def health_check():
    """Health check endpoint — verifies DB, Redis, Ollama connectivity."""
    checks: dict = {"status": "ok", "db": "unknown", "redis": "unknown", "ollama": "unknown"}

    # DB check
    try:
        from app.database import engine
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = f"error: {e}"
        checks["status"] = "degraded"

    # Redis check
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"
        checks["status"] = "degraded"

    # Ollama check
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            if resp.status_code == 200:
                checks["ollama"] = "ok"
            else:
                checks["ollama"] = f"http {resp.status_code}"
                checks["status"] = "degraded"
    except Exception as e:
        checks["ollama"] = f"error: {e}"
        checks["status"] = "degraded"

    return checks

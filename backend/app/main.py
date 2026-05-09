from contextlib import asynccontextmanager
import subprocess
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth, events, providers, scores, tickers, websocket, alerts, admin
from app.core.config import settings
from app.db.session import engine, Base
from app.realtime.redis_client import get_redis_client
import os

log = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("stock_intel.startup")
    # Auto-run migrations on startup
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        log.info("migrations.done")
    except Exception as e:
        log.error("migrations.failed", error=str(e))
    # Auto-seed on first run
    try:
        subprocess.run(["python", "-m", "scripts.seed"], check=True)
        log.info("seed.done")
    except Exception as e:
        log.error("seed.failed", error=str(e))
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    redis = await get_redis_client()
    await redis.ping()
    log.info("redis.connected")
    yield
    log.info("stock_intel.shutdown")

app = FastAPI(title="Stock Intelligence Platform", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,      prefix="/api/auth",      tags=["auth"])
app.include_router(tickers.router,   prefix="/api/tickers",   tags=["tickers"])
app.include_router(events.router,    prefix="/api/events",    tags=["events"])
app.include_router(scores.router,    prefix="/api/scores",    tags=["scores"])
app.include_router(alerts.router,    prefix="/api/alerts",    tags=["alerts"])
app.include_router(providers.router, prefix="/api/providers", tags=["providers"])
app.include_router(admin.router,     prefix="/api/admin",     tags=["admin"])
app.include_router(websocket.router, prefix="/ws",            tags=["websocket"])

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

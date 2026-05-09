"""
Seed script — populates the database with:
  - Demo admin user (admin / admin123)
  - Demo regular user (demo / demo123)
  - Stock symbols for tracked tickers
  - Initial provider health records
"""
import asyncio
from datetime import datetime, timezone

import structlog

from app.db.session import AsyncSessionLocal, engine, Base
from app.models.models import User, StockSymbol, ProviderHealth, Watchlist, WatchlistItem, FreshnessTier
from app.api.routes.auth import get_password_hash

log = structlog.get_logger()

SYMBOLS = [
    {"symbol": "NVDA", "name": "NVIDIA Corporation",      "sector": "Technology",   "exchange": "NASDAQ", "market_cap": 2_400_000_000_000},
    {"symbol": "AAPL", "name": "Apple Inc.",               "sector": "Technology",   "exchange": "NASDAQ", "market_cap": 3_000_000_000_000},
    {"symbol": "TSLA", "name": "Tesla, Inc.",              "sector": "Automotive",   "exchange": "NASDAQ", "market_cap": 680_000_000_000},
    {"symbol": "MSFT", "name": "Microsoft Corporation",    "sector": "Technology",   "exchange": "NASDAQ", "market_cap": 3_100_000_000_000},
    {"symbol": "META", "name": "Meta Platforms, Inc.",     "sector": "Technology",   "exchange": "NASDAQ", "market_cap": 1_300_000_000_000},
    {"symbol": "AMZN", "name": "Amazon.com, Inc.",         "sector": "Consumer",     "exchange": "NASDAQ", "market_cap": 1_900_000_000_000},
    {"symbol": "GOOGL", "name": "Alphabet Inc.",           "sector": "Technology",   "exchange": "NASDAQ", "market_cap": 2_100_000_000_000},
    {"symbol": "AMD",  "name": "Advanced Micro Devices",  "sector": "Technology",   "exchange": "NASDAQ", "market_cap": 240_000_000_000},
]

PROVIDERS = [
    {"name": "mock_news",     "tier": FreshnessTier.POLLED,          "interval": 60},
    {"name": "mock_analyst",  "tier": FreshnessTier.NEAR_REALTIME,   "interval": 120},
    {"name": "mock_insider",  "tier": FreshnessTier.FILING_DELAYED,  "interval": 300},
    {"name": "sec_edgar",     "tier": FreshnessTier.FILING_DELAYED,  "interval": 900},
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # ── Users ────────────────────────────────────────────────────────────
        from sqlalchemy import select

        result = await session.execute(select(User).where(User.username == "admin"))
        if not result.scalar_one_or_none():
            admin = User(
                email="admin@stock-intel.local",
                username="admin",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_admin=True,
            )
            session.add(admin)
            log.info("seed.user", user="admin")

        result = await session.execute(select(User).where(User.username == "demo"))
        if not result.scalar_one_or_none():
            demo = User(
                email="demo@stock-intel.local",
                username="demo",
                hashed_password=get_password_hash("demo123"),
                is_active=True,
                is_admin=False,
            )
            session.add(demo)
            log.info("seed.user", user="demo")

        await session.commit()

        # ── Stock symbols ─────────────────────────────────────────────────────
        for sym in SYMBOLS:
            result = await session.execute(
                select(StockSymbol).where(StockSymbol.symbol == sym["symbol"])
            )
            if not result.scalar_one_or_none():
                session.add(StockSymbol(**sym))
                log.info("seed.symbol", symbol=sym["symbol"])

        # ── Provider health ───────────────────────────────────────────────────
        for p in PROVIDERS:
            result = await session.execute(
                select(ProviderHealth).where(ProviderHealth.provider_name == p["name"])
            )
            if not result.scalar_one_or_none():
                session.add(ProviderHealth(
                    provider_name=p["name"],
                    freshness_tier=p["tier"],
                    poll_interval_s=p["interval"],
                    is_enabled=True,
                    status="unknown",
                ))
                log.info("seed.provider", name=p["name"])

        await session.commit()

        # ── Demo watchlist ────────────────────────────────────────────────────
        result = await session.execute(select(User).where(User.username == "demo"))
        demo_user = result.scalar_one_or_none()
        if demo_user:
            result = await session.execute(
                select(Watchlist).where(Watchlist.user_id == demo_user.id, Watchlist.name == "My Watchlist")
            )
            if not result.scalar_one_or_none():
                wl = Watchlist(user_id=demo_user.id, name="My Watchlist")
                session.add(wl)
                await session.flush()
                for sym in ["NVDA", "AAPL", "TSLA", "MSFT"]:
                    session.add(WatchlistItem(watchlist_id=wl.id, symbol=sym))
                log.info("seed.watchlist", user="demo")

        await session.commit()
        log.info("seed.done")


if __name__ == "__main__":
    asyncio.run(seed())

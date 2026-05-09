"""
Background job scheduler (APScheduler).

Polling intervals are configured per-source to reflect actual data freshness:
  - Mock news:     60 seconds (POLLED)
  - Mock analyst:  120 seconds (NEAR_REALTIME — they don't actually stream)
  - Mock insider:  300 seconds (FILING_DELAYED — filings batch-publish)
  - Scoring:       90 seconds (after events settle)
  - Health check:  30 seconds

Only set intervals < 30s if the provider actually supports streaming/websocket.
"""
import asyncio
import structlog
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.realtime.redis_client import get_redis_client
from app.providers.mock_news import MockNewsAdapter
from app.providers.mock_analyst import MockAnalystAdapter
from app.providers.insider import MockInsiderAdapter
from app.scoring.engine import compute_scores_for_all
from app.models.models import ProviderHealth, StockSymbol

log = structlog.get_logger()

TRACKED_SYMBOLS = ["NVDA", "AAPL", "TSLA", "MSFT", "META", "AMZN", "GOOGL", "AMD"]


async def _update_provider_health(session, provider_name: str, success: bool, error: str = None):
    from sqlalchemy import select
    result = await session.execute(
        select(ProviderHealth).where(ProviderHealth.provider_name == provider_name)
    )
    health = result.scalar_one_or_none()
    if health is None:
        health = ProviderHealth(provider_name=provider_name)
        session.add(health)

    health.last_sync_at = datetime.now(timezone.utc)
    if success:
        health.status = "healthy"
        health.error_count = 0
        health.last_error = None
    else:
        health.status = "degraded"
        health.error_count = (health.error_count or 0) + 1
        health.last_error = error

    await session.commit()


async def poll_news():
    log.info("job.news.start")
    adapter = MockNewsAdapter()
    try:
        async with AsyncSessionLocal() as session:
            redis = await get_redis_client()
            new_count = await adapter.run_cycle(session, redis)
            await _update_provider_health(session, adapter.name, success=True)
            log.info("job.news.done", new_events=new_count)
    except Exception as e:
        log.error("job.news.error", error=str(e))
        async with AsyncSessionLocal() as session:
            await _update_provider_health(session, adapter.name, success=False, error=str(e))


async def poll_analyst():
    log.info("job.analyst.start")
    adapter = MockAnalystAdapter()
    try:
        async with AsyncSessionLocal() as session:
            redis = await get_redis_client()
            new_count = await adapter.run_cycle(session, redis)
            await _update_provider_health(session, adapter.name, success=True)
            log.info("job.analyst.done", new_events=new_count)
    except Exception as e:
        log.error("job.analyst.error", error=str(e))
        async with AsyncSessionLocal() as session:
            await _update_provider_health(session, adapter.name, success=False, error=str(e))


async def poll_insider():
    log.info("job.insider.start")
    adapter = MockInsiderAdapter()
    try:
        async with AsyncSessionLocal() as session:
            redis = await get_redis_client()
            new_count = await adapter.run_cycle(session, redis)
            await _update_provider_health(session, adapter.name, success=True)
            log.info("job.insider.done", new_events=new_count)
    except Exception as e:
        log.error("job.insider.error", error=str(e))
        async with AsyncSessionLocal() as session:
            await _update_provider_health(session, adapter.name, success=False, error=str(e))


async def recalculate_scores():
    log.info("job.scoring.start")
    try:
        async with AsyncSessionLocal() as session:
            scores = await compute_scores_for_all(session, TRACKED_SYMBOLS)
            # Publish updated scores to Redis
            redis = await get_redis_client()
            import json
            for score in scores:
                await redis.publish(f"stock_intel:score:{score.symbol}", json.dumps({
                    "type": "score",
                    "symbol": score.symbol,
                    "total_trade_score": score.total_trade_score,
                    "label": score.label,
                    "news_sentiment_score": score.news_sentiment_score,
                    "analyst_momentum_score": score.analyst_momentum_score,
                    "insider_signal_score": score.insider_signal_score,
                    "price_confirmation_score": score.price_confirmation_score,
                    "scored_at": score.scored_at.isoformat(),
                }))
                await redis.publish("stock_intel:score:ALL", json.dumps({
                    "type": "score",
                    "symbol": score.symbol,
                    "total_trade_score": score.total_trade_score,
                    "label": score.label,
                    "scored_at": score.scored_at.isoformat(),
                }))
            log.info("job.scoring.done", count=len(scores))
    except Exception as e:
        log.error("job.scoring.error", error=str(e))


async def provider_health_check():
    """Check that all providers have synced recently."""
    log.info("job.health_check.start")
    # TODO: implement staleness detection and alerting
    log.info("job.health_check.done")


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")

    scheduler.add_job(poll_news,          IntervalTrigger(seconds=60),  id="poll_news",    replace_existing=True)
    scheduler.add_job(poll_analyst,       IntervalTrigger(seconds=120), id="poll_analyst", replace_existing=True)
    scheduler.add_job(poll_insider,       IntervalTrigger(seconds=300), id="poll_insider", replace_existing=True)
    scheduler.add_job(recalculate_scores, IntervalTrigger(seconds=90),  id="scoring",      replace_existing=True)
    scheduler.add_job(provider_health_check, IntervalTrigger(seconds=30), id="health",     replace_existing=True)

    return scheduler


async def main():
    """Entry point for the standalone worker process."""
    import structlog
    structlog.configure(
        processors=[structlog.dev.ConsoleRenderer()],
    )
    log.info("worker.starting")

    # Run initial jobs immediately
    await poll_news()
    await poll_analyst()
    await poll_insider()
    await recalculate_scores()

    scheduler = build_scheduler()
    scheduler.start()
    log.info("worker.scheduler_started")

    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        log.info("worker.stopped")


if __name__ == "__main__":
    asyncio.run(main())

"""
Mock News Provider Adapter
─────────────────────────
Status: MOCK — returns pre-baked sample data.
Freshness: POLLED (simulated ~60-second polling)

To replace with a real provider:
  1. Set NEWS_PROVIDER=benzinga (or newsapi, polygon) in .env
  2. Set NEWS_API_KEY in .env
  3. Implement a real adapter in providers/news_real.py
  4. Register it in providers/__init__.py

TODO: Real provider integrations:
  - Benzinga Pro API (paid, excellent for catalyst news)
  - NewsAPI.org (free tier available, general news)
  - Polygon.io /vX/reference/news (paid, market-focused)
"""
import hashlib
import json
import random
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

import structlog

from app.models.models import FreshnessTier, NewsEvent
from app.providers.base import BaseProviderAdapter, NormalizedEvent

log = structlog.get_logger()

MOCK_NEWS = [
    {
        "id": "mock-news-001",
        "symbol": "NVDA",
        "headline": "NVIDIA announces record GPU shipments amid AI infrastructure buildout",
        "summary": "NVIDIA's data center segment posts record quarterly revenue driven by H100 demand.",
        "url": "https://example.com/nvda-earnings",
        "published_at": "2024-11-15T09:30:00Z",
        "sentiment": 0.82,
    },
    {
        "id": "mock-news-002",
        "symbol": "AAPL",
        "headline": "Apple Vision Pro returns spike ahead of potential next-gen announcement",
        "summary": "Analysts note elevated return rates for Vision Pro, raising questions about product-market fit.",
        "url": "https://example.com/aapl-vision-pro",
        "published_at": "2024-11-15T10:15:00Z",
        "sentiment": -0.41,
    },
    {
        "id": "mock-news-003",
        "symbol": "TSLA",
        "headline": "Tesla deliveries miss Q3 estimates by 6%; Musk blames macro headwinds",
        "summary": "Tesla delivered 435k vehicles in Q3, below the 463k consensus estimate.",
        "url": "https://example.com/tsla-deliveries",
        "published_at": "2024-11-15T08:00:00Z",
        "sentiment": -0.68,
    },
    {
        "id": "mock-news-004",
        "symbol": "MSFT",
        "headline": "Microsoft Azure revenue accelerates on Copilot enterprise adoption",
        "summary": "Azure grew 29% YoY, beating estimates. Copilot now deployed across 60% of Fortune 500.",
        "url": "https://example.com/msft-azure",
        "published_at": "2024-11-15T11:00:00Z",
        "sentiment": 0.75,
    },
    {
        "id": "mock-news-005",
        "symbol": "META",
        "headline": "Meta's Ray-Ban smart glasses hit 1M units sold — ahead of schedule",
        "summary": "Meta confirms the Ray-Ban collaboration exceeded internal sales targets by Q3.",
        "url": "https://example.com/meta-rayban",
        "published_at": "2024-11-15T07:45:00Z",
        "sentiment": 0.61,
    },
]


class MockNewsAdapter(BaseProviderAdapter):
    name = "mock_news"
    freshness_tier = FreshnessTier.POLLED

    async def fetch_latest(self) -> List[Dict[str, Any]]:
        """Return mock news, adding slight time variation to simulate live polling."""
        now = datetime.now(timezone.utc)
        events = []
        for item in MOCK_NEWS:
            item_copy = item.copy()
            # Randomize timestamp slightly so new polling cycles look fresh
            offset_s = random.randint(-300, 0)
            item_copy["published_at"] = (now + timedelta(seconds=offset_s)).isoformat()
            # Make IDs cycle-unique so we don't always dedupe everything
            item_copy["id"] = f"{item['id']}-{now.strftime('%Y%m%d%H%M')}"
            events.append(item_copy)
        log.info("mock_news.fetched", count=len(events))
        return events

    def normalize(self, raw: Dict[str, Any]) -> NormalizedEvent:
        ts = datetime.fromisoformat(raw["published_at"].replace("Z", "+00:00"))
        sentiment_raw = float(raw.get("sentiment", 0.0))
        dedupe_hash = hashlib.sha256(f"{self.name}:{raw['id']}".encode()).hexdigest()

        return NormalizedEvent(
            source_name=self.name,
            source_event_id=raw["id"],
            event_timestamp=ts,
            symbol=raw["symbol"].upper(),
            freshness_tier=self.freshness_tier,
            raw_payload=raw,
            dedupe_hash=dedupe_hash,
            extra={
                "headline": raw.get("headline", ""),
                "summary": raw.get("summary", ""),
                "url": raw.get("url", ""),
                "sentiment_raw": sentiment_raw,
                "sentiment_score": round(sentiment_raw * 100, 1),
            },
        )

    def validate(self, event: NormalizedEvent) -> bool:
        return bool(event.symbol and event.extra.get("headline"))

    async def upsert_events(self, session, events: List[NormalizedEvent]) -> int:
        from sqlalchemy import select
        new_count = 0
        for event in events:
            # Check for existing dedupe_hash
            result = await session.execute(
                select(NewsEvent).where(NewsEvent.dedupe_hash == event.dedupe_hash)
            )
            if result.scalar_one_or_none():
                continue

            row = NewsEvent(
                symbol=event.symbol,
                source_name=event.source_name,
                source_event_id=event.source_event_id,
                event_timestamp=event.event_timestamp,
                ingested_at=datetime.now(timezone.utc),
                freshness_tier=event.freshness_tier,
                raw_payload=event.raw_payload,
                dedupe_hash=event.dedupe_hash,
                headline=event.extra.get("headline"),
                summary=event.extra.get("summary"),
                url=event.extra.get("url"),
                sentiment_raw=event.extra.get("sentiment_raw"),
                sentiment_score=event.extra.get("sentiment_score"),
            )
            session.add(row)
            new_count += 1

        await session.commit()
        log.info("mock_news.upserted", new=new_count)
        return new_count

    async def publish_updates(self, redis, events: List[NormalizedEvent]) -> None:
        for event in events:
            channel = f"stock_intel:news:{event.symbol}"
            payload = json.dumps({
                "type": "news",
                "symbol": event.symbol,
                "freshness_tier": event.freshness_tier,
                "headline": event.extra.get("headline"),
                "sentiment_score": event.extra.get("sentiment_score"),
                "event_timestamp": event.event_timestamp.isoformat(),
                "source": event.source_name,
            })
            await redis.publish(channel, payload)
            # Also publish to global feed
            await redis.publish("stock_intel:news:ALL", payload)

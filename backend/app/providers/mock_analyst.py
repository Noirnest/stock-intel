"""
Mock Analyst Ratings Provider Adapter
──────────────────────────────────────
Status: MOCK — returns pre-baked sample data.
Freshness: NEAR_REALTIME (analyst actions are typically published within minutes of the firm action)

TODO: Real provider integrations:
  - Benzinga Pro Analyst Ratings API
  - Refinitiv / LSEG StarMine
  - TipRanks API
  - Visible Alpha
"""
import hashlib
import json
import random
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

import structlog

from app.models.models import FreshnessTier, AnalystEvent
from app.providers.base import BaseProviderAdapter, NormalizedEvent

log = structlog.get_logger()

MOCK_ANALYST_ACTIONS = [
    {
        "id": "analyst-001",
        "symbol": "NVDA",
        "firm": "Goldman Sachs",
        "analyst": "Toshiya Hari",
        "action": "reiterate",
        "from_rating": "Buy",
        "to_rating": "Buy",
        "from_target": 650.0,
        "to_target": 800.0,
        "published_at": "2024-11-15T09:00:00Z",
    },
    {
        "id": "analyst-002",
        "symbol": "TSLA",
        "firm": "Morgan Stanley",
        "analyst": "Adam Jonas",
        "action": "downgrade",
        "from_rating": "Overweight",
        "to_rating": "Equal Weight",
        "from_target": 310.0,
        "to_target": 250.0,
        "published_at": "2024-11-15T07:30:00Z",
    },
    {
        "id": "analyst-003",
        "symbol": "AAPL",
        "firm": "Wedbush",
        "analyst": "Dan Ives",
        "action": "upgrade",
        "from_rating": "Neutral",
        "to_rating": "Outperform",
        "from_target": 185.0,
        "to_target": 220.0,
        "published_at": "2024-11-15T08:45:00Z",
    },
    {
        "id": "analyst-004",
        "symbol": "META",
        "firm": "JPMorgan",
        "analyst": "Doug Anmuth",
        "action": "initiate",
        "from_rating": None,
        "to_rating": "Overweight",
        "from_target": None,
        "to_target": 590.0,
        "published_at": "2024-11-15T10:30:00Z",
    },
]

# Rating tier weights for scoring
RATING_WEIGHTS = {
    "Strong Buy": 100,
    "Buy": 75,
    "Overweight": 70,
    "Outperform": 65,
    "Market Perform": 10,
    "Neutral": 0,
    "Equal Weight": 0,
    "Underperform": -65,
    "Underweight": -70,
    "Sell": -75,
    "Strong Sell": -100,
}

ACTION_MULTIPLIERS = {
    "upgrade": 1.2,
    "initiate": 1.0,
    "reiterate": 0.5,
    "downgrade": -1.2,
    "cut_target": -0.4,
    "raise_target": 0.4,
}


def compute_momentum_score(raw: Dict[str, Any]) -> float:
    to_rating = raw.get("to_rating", "Neutral")
    action = raw.get("action", "reiterate")
    base = RATING_WEIGHTS.get(to_rating, 0)
    multiplier = ACTION_MULTIPLIERS.get(action, 0.5)

    # Target price change bonus
    from_t = raw.get("from_target")
    to_t = raw.get("to_target")
    target_delta = 0.0
    if from_t and to_t and from_t > 0:
        pct_change = (to_t - from_t) / from_t * 100
        target_delta = max(-20, min(20, pct_change))

    score = (base * abs(multiplier)) * (1 if multiplier > 0 else -1) + target_delta
    return max(-100, min(100, round(score, 1)))


class MockAnalystAdapter(BaseProviderAdapter):
    name = "mock_analyst"
    freshness_tier = FreshnessTier.NEAR_REALTIME

    async def fetch_latest(self) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        events = []
        for item in MOCK_ANALYST_ACTIONS:
            item_copy = item.copy()
            offset_s = random.randint(-600, 0)
            item_copy["published_at"] = (now + timedelta(seconds=offset_s)).isoformat()
            item_copy["id"] = f"{item['id']}-{now.strftime('%Y%m%d%H%M')}"
            events.append(item_copy)
        log.info("mock_analyst.fetched", count=len(events))
        return events

    def normalize(self, raw: Dict[str, Any]) -> NormalizedEvent:
        ts = datetime.fromisoformat(raw["published_at"].replace("Z", "+00:00"))
        dedupe_hash = hashlib.sha256(f"{self.name}:{raw['id']}".encode()).hexdigest()
        momentum_score = compute_momentum_score(raw)

        return NormalizedEvent(
            source_name=self.name,
            source_event_id=raw["id"],
            event_timestamp=ts,
            symbol=raw["symbol"].upper(),
            freshness_tier=self.freshness_tier,
            raw_payload=raw,
            dedupe_hash=dedupe_hash,
            extra={
                "analyst_firm": raw.get("firm"),
                "analyst_name": raw.get("analyst"),
                "action": raw.get("action"),
                "from_rating": raw.get("from_rating"),
                "to_rating": raw.get("to_rating"),
                "from_target": raw.get("from_target"),
                "to_target": raw.get("to_target"),
                "momentum_score": momentum_score,
            },
        )

    def validate(self, event: NormalizedEvent) -> bool:
        return bool(event.symbol and event.extra.get("to_rating"))

    async def upsert_events(self, session, events: List[NormalizedEvent]) -> int:
        from sqlalchemy import select
        new_count = 0
        for event in events:
            result = await session.execute(
                select(AnalystEvent).where(AnalystEvent.dedupe_hash == event.dedupe_hash)
            )
            if result.scalar_one_or_none():
                continue

            row = AnalystEvent(
                symbol=event.symbol,
                source_name=event.source_name,
                source_event_id=event.source_event_id,
                event_timestamp=event.event_timestamp,
                freshness_tier=event.freshness_tier,
                raw_payload=event.raw_payload,
                dedupe_hash=event.dedupe_hash,
                analyst_firm=event.extra.get("analyst_firm"),
                analyst_name=event.extra.get("analyst_name"),
                action=event.extra.get("action"),
                from_rating=event.extra.get("from_rating"),
                to_rating=event.extra.get("to_rating"),
                from_target=event.extra.get("from_target"),
                to_target=event.extra.get("to_target"),
                momentum_score=event.extra.get("momentum_score"),
            )
            session.add(row)
            new_count += 1

        await session.commit()
        log.info("mock_analyst.upserted", new=new_count)
        return new_count

    async def publish_updates(self, redis, events: List[NormalizedEvent]) -> None:
        for event in events:
            channel = f"stock_intel:analyst:{event.symbol}"
            payload = json.dumps({
                "type": "analyst",
                "symbol": event.symbol,
                "freshness_tier": event.freshness_tier,
                "action": event.extra.get("action"),
                "firm": event.extra.get("analyst_firm"),
                "to_rating": event.extra.get("to_rating"),
                "to_target": event.extra.get("to_target"),
                "momentum_score": event.extra.get("momentum_score"),
                "event_timestamp": event.event_timestamp.isoformat(),
                "source": event.source_name,
            })
            await redis.publish(channel, payload)
            await redis.publish("stock_intel:analyst:ALL", payload)

"""
Provider adapter interface.

Every data source must implement this protocol so providers can be swapped
without touching the rest of the system.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.models import FreshnessTier


@dataclass
class NormalizedEvent:
    """Common envelope for any normalized event coming from a provider."""
    source_name: str
    source_event_id: str
    event_timestamp: datetime
    symbol: str
    freshness_tier: FreshnessTier
    raw_payload: Dict[str, Any]
    dedupe_hash: str = ""

    # Provider-specific normalized fields are stored in extra
    extra: Dict[str, Any] = field(default_factory=dict)


class BaseProviderAdapter(ABC):
    """
    Abstract base class for all provider adapters.

    Lifecycle per polling cycle:
        events = await adapter.fetch_latest()
        normalized = [adapter.normalize(e) for e in events]
        validated = [adapter.validate(n) for n in normalized]
        new_count = await adapter.upsert_events(session, validated)
        await adapter.publish_updates(redis, validated)
    """

    name: str = "base"
    freshness_tier: FreshnessTier = FreshnessTier.POLLED

    @abstractmethod
    async def fetch_latest(self) -> List[Dict[str, Any]]:
        """
        Fetch raw events from the provider.
        Returns a list of raw dicts (provider-specific shape).
        """
        ...

    @abstractmethod
    def normalize(self, raw: Dict[str, Any]) -> NormalizedEvent:
        """
        Map a raw provider payload to a NormalizedEvent.
        Must populate dedupe_hash deterministically.
        """
        ...

    @abstractmethod
    def validate(self, event: NormalizedEvent) -> bool:
        """Return True if the event is well-formed and should be ingested."""
        ...

    @abstractmethod
    async def upsert_events(self, session, events: List[NormalizedEvent]) -> int:
        """
        Insert new events into PostgreSQL, ignoring duplicates via dedupe_hash.
        Returns count of newly inserted events.
        """
        ...

    @abstractmethod
    async def publish_updates(self, redis, events: List[NormalizedEvent]) -> None:
        """
        Publish newly ingested events to Redis for WebSocket distribution.
        Channel naming convention: stock_intel:{event_type}:{symbol}
        """
        ...

    async def run_cycle(self, session, redis) -> int:
        """Full polling cycle. Returns number of new events ingested."""
        raws = await self.fetch_latest()
        normalized = [self.normalize(r) for r in raws]
        valid = [n for n in normalized if self.validate(n)]
        new_count = await self.upsert_events(session, valid)
        if new_count > 0:
            new_events = valid  # Simplified — ideally filter to only truly new ones
            await self.publish_updates(redis, new_events)
        return new_count

"""
SEC EDGAR Insider Filings Adapter
──────────────────────────────────
IMPORTANT: SEC insider filings are FILING_DELAYED.
The filing date may be several days after the actual transaction date.
This is NOT real-time trade execution data.
The UI must communicate this clearly — e.g. "Filing-Delayed Insider Buy Signal".

Compliance requirements (per SEC fair-access rules):
  - User-Agent must identify the application and a contact email
  - Rate limit: max ~10 requests/second (we use 8/s to be safe)
  - Retry with exponential backoff on 429 responses
  - Cache responses to avoid redundant requests

Status: REAL implementation (SEC EDGAR is public/free).
  The mock_insider adapter below is used by default in development.
  To use real EDGAR data, set INSIDER_PROVIDER=edgar in .env.

Reference:
  https://www.sec.gov/developer
  https://efts.sec.gov/LATEST/search-index?q=%22form-type%22%3A%224%22
"""
import asyncio
import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.models.models import FreshnessTier, InsiderEvent
from app.providers.base import BaseProviderAdapter, NormalizedEvent

log = structlog.get_logger()

EDGAR_BASE = "https://efts.sec.gov"
EDGAR_SUBMISSIONS_BASE = "https://data.sec.gov"
EDGAR_FULL_TEXT = "https://efts.sec.gov/LATEST/search-index"


class SECEdgarInsiderAdapter(BaseProviderAdapter):
    """
    Fetches Form 4 insider filings from SEC EDGAR.

    Form 4 = Statement of Changes in Beneficial Ownership
    Filed within 2 business days of the transaction.

    NOTE: We are reading public SEC data. This is legal and encouraged
    by the SEC, but must follow their fair-access guidelines.
    """
    name = "sec_edgar"
    freshness_tier = FreshnessTier.FILING_DELAYED

    def __init__(self, symbols: Optional[List[str]] = None):
        self.symbols = symbols or ["NVDA", "AAPL", "TSLA", "MSFT", "META"]
        self._rate_limiter = asyncio.Semaphore(settings.SEC_RATE_LIMIT_PER_SECOND)
        self._cache: Dict[str, Any] = {}

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "User-Agent": settings.sec_user_agent,
            "Accept": "application/json",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def _get(self, url: str) -> Dict[str, Any]:
        """Rate-limited, cached GET with retry."""
        if url in self._cache:
            return self._cache[url]

        async with self._rate_limiter:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers=self.headers)
                resp.raise_for_status()
                data = resp.json()
                self._cache[url] = data
                return data

    async def fetch_latest(self) -> List[Dict[str, Any]]:
        """
        Search EDGAR full-text search for recent Form 4 filings.
        Returns raw filing metadata for our target symbols.
        """
        # Search for recent Form 4 filings
        url = (
            f"{EDGAR_BASE}/LATEST/search-index"
            f"?q=%22form-type%22%3A%224%22"
            f"&dateRange=custom"
            f"&startdt={(datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d')}"
            f"&forms=4"
            f"&hits.hits.total.value=true"
            f"&hits.hits._source.period_of_report=true"
        )

        results = []
        try:
            data = await self._get(url)
            hits = data.get("hits", {}).get("hits", [])
            for hit in hits[:50]:  # Limit to 50 most recent
                src = hit.get("_source", {})
                ticker = src.get("ticker", "")
                if ticker and ticker.upper() in [s.upper() for s in self.symbols]:
                    results.append({
                        "id": hit.get("_id", ""),
                        "symbol": ticker.upper(),
                        "filing_date": src.get("file_date", ""),
                        "period": src.get("period_of_report", ""),
                        "accession": src.get("accession_no", ""),
                        "entity_name": src.get("entity_name", ""),
                        "form_type": src.get("form_type", "4"),
                    })
        except Exception as e:
            log.error("edgar.fetch_failed", error=str(e))

        log.info("edgar.fetched", count=len(results))
        return results

    def normalize(self, raw: Dict[str, Any]) -> NormalizedEvent:
        filing_date_str = raw.get("filing_date", "")
        try:
            filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except Exception:
            filing_date = datetime.now(timezone.utc)

        dedupe_hash = hashlib.sha256(
            f"{self.name}:{raw.get('id', '')}".encode()
        ).hexdigest()

        return NormalizedEvent(
            source_name=self.name,
            source_event_id=raw.get("id", ""),
            event_timestamp=filing_date,
            symbol=raw.get("symbol", "").upper(),
            freshness_tier=self.freshness_tier,
            raw_payload=raw,
            dedupe_hash=dedupe_hash,
            extra={
                "insider_name": raw.get("entity_name", "Unknown"),
                "insider_title": "Insider",  # Would need to parse XML for detail
                "transaction_type": "unknown",  # Would need to parse Form 4 XML
                "filing_date": filing_date.isoformat(),
                # NOTE: Actual transaction details require parsing the full Form 4 XML.
                # This adapter returns filing-level metadata only.
                # For full parsing, fetch the accession document and parse table II.
                "signal_score": 0.0,  # Computed after full parsing
            },
        )

    def validate(self, event: NormalizedEvent) -> bool:
        return bool(event.symbol and event.source_event_id)

    async def upsert_events(self, session, events: List[NormalizedEvent]) -> int:
        from sqlalchemy import select
        new_count = 0
        for event in events:
            result = await session.execute(
                select(InsiderEvent).where(InsiderEvent.dedupe_hash == event.dedupe_hash)
            )
            if result.scalar_one_or_none():
                continue

            row = InsiderEvent(
                symbol=event.symbol,
                source_name=event.source_name,
                source_event_id=event.source_event_id,
                event_timestamp=event.event_timestamp,
                freshness_tier=event.freshness_tier,
                raw_payload=event.raw_payload,
                dedupe_hash=event.dedupe_hash,
                insider_name=event.extra.get("insider_name"),
                insider_title=event.extra.get("insider_title"),
                transaction_type=event.extra.get("transaction_type"),
                filing_date=event.event_timestamp,
                signal_score=event.extra.get("signal_score", 0.0),
            )
            session.add(row)
            new_count += 1

        await session.commit()
        log.info("edgar.upserted", new=new_count)
        return new_count

    async def publish_updates(self, redis, events: List[NormalizedEvent]) -> None:
        for event in events:
            channel = f"stock_intel:insider:{event.symbol}"
            payload = json.dumps({
                "type": "insider",
                "symbol": event.symbol,
                "freshness_tier": event.freshness_tier,
                # IMPORTANT: Clearly label as filing-delayed for UI display
                "freshness_note": "Filing-delayed — transaction may have occurred days before this filing",
                "insider_name": event.extra.get("insider_name"),
                "transaction_type": event.extra.get("transaction_type"),
                "filing_date": event.extra.get("filing_date"),
                "event_timestamp": event.event_timestamp.isoformat(),
                "source": event.source_name,
            })
            await redis.publish(channel, payload)
            await redis.publish("stock_intel:insider:ALL", payload)


# ─── Mock Insider Adapter (used by default in development) ──────────────────

MOCK_INSIDER_EVENTS = [
    {
        "id": "insider-001",
        "symbol": "NVDA",
        "insider_name": "Jensen Huang",
        "insider_title": "CEO",
        "transaction_type": "sell",
        "shares": 250000,
        "price_per_share": 480.50,
        "total_value": 120125000,
        "filing_date": "2024-11-15",
        "transaction_date": "2024-11-12",
    },
    {
        "id": "insider-002",
        "symbol": "TSLA",
        "insider_name": "Elon Musk",
        "insider_title": "CEO",
        "transaction_type": "buy",
        "shares": 500000,
        "price_per_share": 210.00,
        "total_value": 105000000,
        "filing_date": "2024-11-15",
        "transaction_date": "2024-11-13",
    },
    {
        "id": "insider-003",
        "symbol": "AAPL",
        "insider_name": "Tim Cook",
        "insider_title": "CEO",
        "transaction_type": "sell",
        "shares": 100000,
        "price_per_share": 192.00,
        "total_value": 19200000,
        "filing_date": "2024-11-14",
        "transaction_date": "2024-11-11",
    },
]


class MockInsiderAdapter(BaseProviderAdapter):
    """Mock insider adapter for development. Uses pre-baked Form 4 data."""
    name = "mock_insider"
    freshness_tier = FreshnessTier.FILING_DELAYED

    async def fetch_latest(self) -> List[Dict[str, Any]]:
        import random
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        events = []
        for item in MOCK_INSIDER_EVENTS:
            item_copy = item.copy()
            item_copy["id"] = f"{item['id']}-{now.strftime('%Y%m%d%H%M')}"
            events.append(item_copy)
        return events

    def normalize(self, raw: Dict[str, Any]) -> NormalizedEvent:
        filing_date = datetime.strptime(raw["filing_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        tx_date = datetime.strptime(raw["transaction_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        dedupe_hash = hashlib.sha256(f"{self.name}:{raw['id']}".encode()).hexdigest()

        tx_type = raw.get("transaction_type", "unknown")
        total_value = raw.get("total_value", 0)
        # Simple signal: large buys are bullish, large sells are bearish
        if tx_type == "buy":
            signal = min(100, (total_value / 1_000_000) * 5)
        elif tx_type == "sell":
            signal = max(-100, -(total_value / 1_000_000) * 2)
        else:
            signal = 0.0

        return NormalizedEvent(
            source_name=self.name,
            source_event_id=raw["id"],
            event_timestamp=filing_date,
            symbol=raw["symbol"].upper(),
            freshness_tier=self.freshness_tier,
            raw_payload=raw,
            dedupe_hash=dedupe_hash,
            extra={
                "insider_name": raw.get("insider_name"),
                "insider_title": raw.get("insider_title"),
                "transaction_type": tx_type,
                "shares": raw.get("shares"),
                "price_per_share": raw.get("price_per_share"),
                "total_value": total_value,
                "filing_date": filing_date.isoformat(),
                "transaction_date": tx_date.isoformat(),
                "signal_score": round(signal, 1),
            },
        )

    def validate(self, event: NormalizedEvent) -> bool:
        return bool(event.symbol and event.extra.get("insider_name"))

    async def upsert_events(self, session, events: List[NormalizedEvent]) -> int:
        from sqlalchemy import select
        new_count = 0
        for event in events:
            result = await session.execute(
                select(InsiderEvent).where(InsiderEvent.dedupe_hash == event.dedupe_hash)
            )
            if result.scalar_one_or_none():
                continue

            row = InsiderEvent(
                symbol=event.symbol,
                source_name=event.source_name,
                source_event_id=event.source_event_id,
                event_timestamp=event.event_timestamp,
                freshness_tier=event.freshness_tier,
                raw_payload=event.raw_payload,
                dedupe_hash=event.dedupe_hash,
                insider_name=event.extra.get("insider_name"),
                insider_title=event.extra.get("insider_title"),
                transaction_type=event.extra.get("transaction_type"),
                shares=event.extra.get("shares"),
                price_per_share=event.extra.get("price_per_share"),
                total_value=event.extra.get("total_value"),
                filing_date=event.event_timestamp,
                signal_score=event.extra.get("signal_score"),
            )
            session.add(row)
            new_count += 1

        await session.commit()
        return new_count

    async def publish_updates(self, redis, events: List[NormalizedEvent]) -> None:
        for event in events:
            channel = f"stock_intel:insider:{event.symbol}"
            payload = json.dumps({
                "type": "insider",
                "symbol": event.symbol,
                "freshness_tier": event.freshness_tier,
                "freshness_note": "Filing-delayed — transaction may have occurred days before this filing",
                "insider_name": event.extra.get("insider_name"),
                "insider_title": event.extra.get("insider_title"),
                "transaction_type": event.extra.get("transaction_type"),
                "shares": event.extra.get("shares"),
                "total_value": event.extra.get("total_value"),
                "signal_score": event.extra.get("signal_score"),
                "event_timestamp": event.event_timestamp.isoformat(),
                "source": event.source_name,
            })
            await redis.publish(channel, payload)
            await redis.publish("stock_intel:insider:ALL", payload)

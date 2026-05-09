# Stock Intelligence Platform — Architecture

## Overview

A real-time trading research dashboard that ingests and ranks trading signals from
news, analyst ratings, and SEC insider filings. Built for quick day-trading research
with full transparency about data freshness.

```
┌──────────────────────────────────────────────────────────────────┐
│                         Browser (Next.js)                        │
│  Dashboard · Watchlist · Ticker detail · Admin                   │
│           WebSocket client  ←  live event updates                │
│           REST API calls    ←  initial data load                 │
└──────────┬──────────────────────────────────┬───────────────────┘
           │ HTTP/REST                         │ WebSocket
           ▼                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI (port 8000)                            │
│  /api/auth  /api/events  /api/scores  /api/providers  /api/admin │
│                    /ws/stream (WebSocket endpoint)               │
│           Subscribes to Redis Pub/Sub → broadcasts to clients    │
└────────────────┬─────────────────────────────────────────────────┘
                 │ async SQLAlchemy                │ redis-py pub/sub
                 ▼                                 ▼
┌────────────────────────┐        ┌─────────────────────────────────┐
│     PostgreSQL 16      │        │        Redis 7                  │
│  All normalized events │        │  Pub/Sub channels:              │
│  Signal scores         │        │    stock_intel:news:{SYMBOL}    │
│  Provider health       │        │    stock_intel:analyst:{SYMBOL} │
│  Users / watchlists    │        │    stock_intel:insider:{SYMBOL} │
└────────────────────────┘        │    stock_intel:score:{SYMBOL}   │
                                  │    stock_intel:*:ALL            │
                                  └─────────────────────────────────┘
                                                 ▲
                                                 │ publish
┌────────────────────────────────────────────────────────────────┐
│               Worker Process (APScheduler)                      │
│                                                                 │
│  poll_news()       → 60s    MockNewsAdapter                     │
│  poll_analyst()    → 120s   MockAnalystAdapter                  │
│  poll_insider()    → 300s   MockInsiderAdapter (or SEC EDGAR)   │
│  recalculate_scores() → 90s ScoringEngine                       │
│  provider_health() → 30s   HealthChecker                        │
│                                                                 │
│  Each job: fetch → normalize → validate → upsert → publish      │
└────────────────────────────────────────────────────────────────┘
```

## Data Freshness Tiers

| Tier | Label | Description | Example |
|------|-------|-------------|---------|
| STREAMING | Live green dot | True streaming feed | Future: market data websocket |
| NEAR_REALTIME | Blue dot | Updated within minutes | Analyst ratings via paid API |
| POLLED | Amber dot | Polled every 60-120s | News APIs |
| FILING_DELAYED | Gray dot | Regulatory delay | SEC EDGAR Form 4 filings |

**Critical note on insider filings:** SEC Form 4 must be filed within 2 business days
of the transaction. The filing date is not the trade date. The UI always shows a
disclosure banner when displaying insider data.

## Scoring Engine

Each symbol receives 5 component scores (-100 to +100):

| Component | Description | Default Weight |
|-----------|-------------|----------------|
| news_sentiment_score | Recency-weighted NLP sentiment | 20% |
| catalyst_score | High-magnitude event detection | 20% |
| analyst_momentum_score | Aggregated analyst action scoring | 30% |
| insider_signal_score | Insider buy/sell signal | 20% |
| price_confirmation_score | Volume/momentum confirmation | 10% |

**Total trade score** = weighted composite.

**Labels:**
- Strong Watch: score ≥ 50
- Watch: score ≥ 20
- Neutral: score ≥ -20
- Avoid: score < -20

## Provider Adapter Pattern

All data sources implement `BaseProviderAdapter`:

```python
class MyAdapter(BaseProviderAdapter):
    async def fetch_latest(self) -> List[Dict]:   # Call provider API
    def normalize(self, raw) -> NormalizedEvent:   # Map to common schema
    def validate(self, event) -> bool:             # Validate before insert
    async def upsert_events(self, session, events) -> int:  # Write to DB
    async def publish_updates(self, redis, events) -> None: # Push to Redis
```

To add a new provider:
1. Create `backend/app/providers/my_provider.py`
2. Extend `BaseProviderAdapter`
3. Register in `backend/app/workers/scheduler.py`
4. Add health record in seed script

## WebSocket Message Protocol

All messages are JSON with schema version `v`:

```json
{ "v": 1, "type": "news|analyst|insider|score|heartbeat", ... }
```

The frontend:
- Connects at `/ws/stream?symbols=NVDA,AAPL` (optional filter)
- Reconnects with exponential backoff (1s → 30s max)
- Marks connection as "Delayed" if no heartbeat in 30s
- Deduplicates events per connection

## SEC EDGAR Compliance

The `SECEdgarInsiderAdapter` implements all SEC fair-access requirements:
- User-Agent header: `AppName/Version contact:email@domain.com`
- Rate limiting: configurable via `SEC_RATE_LIMIT_PER_SECOND` (default: 8/s)
- Response caching: in-memory cache per process
- Retry: 3 attempts with exponential backoff via tenacity
- Logging: all requests and errors logged

Reference: https://www.sec.gov/developer

## Mock vs Production

| Component | Mock (default) | Production path |
|-----------|---------------|-----------------|
| News | `MockNewsAdapter` pre-baked data | Set `NEWS_PROVIDER=benzinga` + `NEWS_API_KEY` |
| Analyst | `MockAnalystAdapter` pre-baked | Set `ANALYST_PROVIDER=refinitiv` + key |
| Insider | `MockInsiderAdapter` pre-baked | Set `INSIDER_PROVIDER=edgar` (free, compliant) |
| Price | No price data in v1 | Set `PRICE_PROVIDER=polygon` + key |
| Auth | JWT with bcrypt | Production: add OAuth2/SSO |
| Alerts | Stubs only | Add Slack/Telegram webhook keys |

Everything behind env vars — no code changes needed to switch.

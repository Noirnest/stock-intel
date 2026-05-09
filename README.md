# Stock Intelligence Platform

A production-grade real-time trading research dashboard. Ingests and ranks trading signals from news, analyst ratings, and SEC insider filings. Built for transparency — every data point shows its freshness tier.

> **Disclaimer:** This is a research tool. Nothing here is financial advice. Signal scores are for informational analysis only.

---

## Quick Start

```bash
# 1. Clone the repo
git clone <repo> stock-intel && cd stock-intel

# 2. Copy environment config
cp .env.example .env

# 3. Start everything
make up

# 4. Run migrations and seed data
make migrate
make seed

# 5. Open the app
open http://localhost:3000
```

**Demo credentials:**
- User: `demo` / `demo123`
- Admin: `admin` / `admin123`

---

## Architecture

```
Next.js (3000) → FastAPI (8000) → PostgreSQL + Redis
                      ↑
              Worker (APScheduler)
              polls providers → publishes to Redis → WebSocket → browser
```

See [docs/architecture.md](docs/architecture.md) for the full diagram.

---

## Services

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Next.js dashboard |
| Backend API | http://localhost:8000 | FastAPI |
| API Docs | http://localhost:8000/docs | Swagger UI |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Pub/Sub + cache |

---

## Pages

| Route | Description |
|-------|-------------|
| `/login` | Authentication |
| `/dashboard` | Main research dashboard |
| `/watchlist` | Score cards for tracked symbols |
| `/alerts` | Alert configuration (stub) |
| `/ticker/[SYMBOL]` | Per-symbol deep dive + "Why this stock?" |
| `/admin/providers` | Provider health, enable/disable, intervals |
| `/admin/scoring` | Weight editor + live scoring tester |

---

## Data Freshness

Every data point shows its freshness tier:

| Badge | Meaning |
|-------|---------|
| 🟢 STREAMING | True real-time stream |
| 🔵 NEAR-RT | Updated within minutes |
| 🟡 POLLED | Polled every 60–120s |
| ⚫ FILING-DELAYED | SEC regulatory delay (may be days) |

---

## Adding Real Providers

Set in `.env` and restart:

```bash
# News (Benzinga, NewsAPI, Polygon)
NEWS_PROVIDER=benzinga
NEWS_API_KEY=your_key_here

# Analyst (Benzinga, Refinitiv)
ANALYST_PROVIDER=benzinga
ANALYST_API_KEY=your_key_here

# Market Price (Polygon, Alpaca)
PRICE_PROVIDER=polygon
PRICE_API_KEY=your_key_here

# SEC EDGAR (free, compliant — requires only your contact info)
SEC_USER_AGENT_APP=MyApp/1.0
SEC_USER_AGENT_EMAIL=you@yourdomain.com
```

---

## Development Commands

```bash
make up           # Start all services
make down         # Stop all services
make logs         # Tail all logs
make migrate      # Run DB migrations
make seed         # Seed demo data
make reset        # Full reset (⚠ data loss)
make shell-backend  # Shell into backend container
make shell-db       # psql session
```

---

## Project Structure

```
stock-intel/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # FastAPI route handlers
│   │   ├── core/            # Config, settings
│   │   ├── db/              # Session, engine
│   │   ├── models/          # SQLAlchemy models
│   │   ├── providers/       # Provider adapters (mock + SEC EDGAR)
│   │   ├── realtime/        # Redis client
│   │   ├── scoring/         # Scoring engine
│   │   └── workers/         # APScheduler jobs
│   ├── alembic/             # DB migrations
│   └── scripts/             # Seed script
├── frontend/
│   ├── app/                 # Next.js App Router pages
│   ├── components/          # UI components
│   ├── hooks/               # useWebSocket
│   ├── services/            # API client
│   ├── stores/              # Zustand WS store
│   └── types/               # TypeScript types
├── docs/                    # Architecture docs
├── mock-data/               # Sample JSON payloads
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## Mock vs Production Status

| Component | Status | Notes |
|-----------|--------|-------|
| News provider | ✅ Mock (pre-baked) | Plug in Benzinga/NewsAPI via env |
| Analyst provider | ✅ Mock (pre-baked) | Plug in Refinitiv/Benzinga |
| Insider filings | ✅ Mock + SEC EDGAR adapter | EDGAR adapter is real & compliant |
| Scoring engine | ✅ Production-ready | All 5 dimensions, weighted composite |
| WebSocket pipeline | ✅ Production-ready | Redis pub/sub → WS → browser |
| Auth (JWT) | ✅ Working | v1 local auth; add SSO for production |
| Price data | 🔲 Stub only | Add Polygon/Alpaca in PRICE_PROVIDER |
| Alerts delivery | 🔲 Stubs only | Webhook/email/Telegram backend scaffold |
| Alert UI | 🔲 v2 | Backend models + API routes ready |

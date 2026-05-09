"""
Database models for Stock Intelligence Platform.

Every event table includes:
- id, symbol, source_name, source_event_id
- provider_timestamp, ingested_at, event_timestamp
- freshness_tier, raw_payload (JSONB), dedupe_hash
"""
import hashlib
import json
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, UniqueConstraint, Enum,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─── Enumerations ───────────────────────────────────────────────────────────

class FreshnessTier(str, PyEnum):
    STREAMING       = "STREAMING"
    NEAR_REALTIME   = "NEAR_REALTIME"
    POLLED          = "POLLED"
    FILING_DELAYED  = "FILING_DELAYED"


class AlertType(str, PyEnum):
    BREAKING_NEWS      = "BREAKING_NEWS"
    ANALYST_ACTION     = "ANALYST_ACTION"
    INSIDER_EVENT      = "INSIDER_EVENT"
    SCORE_THRESHOLD    = "SCORE_THRESHOLD"
    PRICE_CONFIRMATION = "PRICE_CONFIRMATION"


class AlertChannel(str, PyEnum):
    IN_APP   = "IN_APP"
    WEBHOOK  = "WEBHOOK"
    EMAIL    = "EMAIL"
    TELEGRAM = "TELEGRAM"
    SLACK    = "SLACK"


class SignalLabel(str, PyEnum):
    STRONG_WATCH = "STRONG_WATCH"
    WATCH        = "WATCH"
    NEUTRAL      = "NEUTRAL"
    AVOID        = "AVOID"


# ─── Users ──────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    username      = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active     = Column(Boolean, default=True)
    is_admin      = Column(Boolean, default=False)
    created_at    = Column(DateTime(timezone=True), default=utcnow)
    updated_at    = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    watchlists    = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    alerts        = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    notes         = relationship("UserNote", back_populates="user", cascade="all, delete-orphan")


# ─── Watchlists ──────────────────────────────────────────────────────────────

class Watchlist(Base):
    __tablename__ = "watchlists"

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    name       = Column(String(100), nullable=False, default="Default")
    created_at = Column(DateTime(timezone=True), default=utcnow)

    user       = relationship("User", back_populates="watchlists")
    items      = relationship("WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan")


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (UniqueConstraint("watchlist_id", "symbol"),)

    id           = Column(Integer, primary_key=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id"), nullable=False)
    symbol       = Column(String(20), nullable=False, index=True)
    added_at     = Column(DateTime(timezone=True), default=utcnow)

    watchlist    = relationship("Watchlist", back_populates="items")


# ─── Stock Symbols ───────────────────────────────────────────────────────────

class StockSymbol(Base):
    __tablename__ = "stock_symbols"

    id          = Column(Integer, primary_key=True)
    symbol      = Column(String(20), unique=True, nullable=False, index=True)
    name        = Column(String(255))
    sector      = Column(String(100))
    industry    = Column(String(100))
    market_cap  = Column(Float)        # USD, approximate
    exchange    = Column(String(20))
    country     = Column(String(50))
    is_active   = Column(Boolean, default=True)
    updated_at  = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ─── News Events ─────────────────────────────────────────────────────────────

class NewsEvent(Base):
    __tablename__ = "news_events"
    __table_args__ = (
        UniqueConstraint("source_name", "source_event_id"),
        Index("ix_news_events_symbol_ts", "symbol", "event_timestamp"),
    )

    id               = Column(Integer, primary_key=True)
    symbol           = Column(String(20), nullable=False, index=True)
    source_name      = Column(String(100), nullable=False)
    source_event_id  = Column(String(255), nullable=False)
    provider_timestamp = Column(DateTime(timezone=True))
    ingested_at      = Column(DateTime(timezone=True), default=utcnow)
    event_timestamp  = Column(DateTime(timezone=True), nullable=False, index=True)
    freshness_tier   = Column(Enum(FreshnessTier), default=FreshnessTier.POLLED)
    raw_payload      = Column(JSONB)
    dedupe_hash      = Column(String(64), unique=True)

    # Normalized fields
    headline         = Column(Text)
    summary          = Column(Text)
    url              = Column(Text)
    sentiment_raw    = Column(Float)    # -1.0 to 1.0 from NLP
    sentiment_score  = Column(Float)    # -100 to 100 scaled

    @staticmethod
    def compute_hash(source_name: str, source_event_id: str) -> str:
        return hashlib.sha256(f"{source_name}:{source_event_id}".encode()).hexdigest()


# ─── Analyst Events ──────────────────────────────────────────────────────────

class AnalystEvent(Base):
    __tablename__ = "analyst_events"
    __table_args__ = (
        UniqueConstraint("source_name", "source_event_id"),
        Index("ix_analyst_events_symbol_ts", "symbol", "event_timestamp"),
    )

    id               = Column(Integer, primary_key=True)
    symbol           = Column(String(20), nullable=False, index=True)
    source_name      = Column(String(100), nullable=False)
    source_event_id  = Column(String(255), nullable=False)
    provider_timestamp = Column(DateTime(timezone=True))
    ingested_at      = Column(DateTime(timezone=True), default=utcnow)
    event_timestamp  = Column(DateTime(timezone=True), nullable=False, index=True)
    freshness_tier   = Column(Enum(FreshnessTier), default=FreshnessTier.NEAR_REALTIME)
    raw_payload      = Column(JSONB)
    dedupe_hash      = Column(String(64), unique=True)

    # Normalized fields
    analyst_firm     = Column(String(255))
    analyst_name     = Column(String(255))
    action           = Column(String(50))    # e.g. "upgrade", "downgrade", "initiate"
    from_rating      = Column(String(50))
    to_rating        = Column(String(50))
    from_target      = Column(Float)
    to_target        = Column(Float)
    momentum_score   = Column(Float)         # -100 to 100


# ─── Insider Events ──────────────────────────────────────────────────────────

class InsiderEvent(Base):
    __tablename__ = "insider_events"
    __table_args__ = (
        UniqueConstraint("source_name", "source_event_id"),
        Index("ix_insider_events_symbol_ts", "symbol", "event_timestamp"),
    )

    id               = Column(Integer, primary_key=True)
    symbol           = Column(String(20), nullable=False, index=True)
    source_name      = Column(String(100), nullable=False)
    source_event_id  = Column(String(255), nullable=False)
    provider_timestamp = Column(DateTime(timezone=True))
    ingested_at      = Column(DateTime(timezone=True), default=utcnow)
    event_timestamp  = Column(DateTime(timezone=True), nullable=False, index=True)
    # NOTE: SEC EDGAR insider filings are FILING_DELAYED — not real-time trade execution data.
    # The filing date may be days after the actual transaction. The UI must communicate this clearly.
    freshness_tier   = Column(Enum(FreshnessTier), default=FreshnessTier.FILING_DELAYED)
    raw_payload      = Column(JSONB)
    dedupe_hash      = Column(String(64), unique=True)

    # Normalized fields
    insider_name     = Column(String(255))
    insider_title    = Column(String(255))
    transaction_type = Column(String(50))  # "buy" | "sell" | "option_exercise"
    shares           = Column(Float)
    price_per_share  = Column(Float)
    total_value      = Column(Float)
    filing_date      = Column(DateTime(timezone=True))
    transaction_date = Column(DateTime(timezone=True))  # may differ from filing_date
    signal_score     = Column(Float)       # -100 to 100


# ─── Price Snapshots ─────────────────────────────────────────────────────────

class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"
    __table_args__ = (
        Index("ix_price_snapshots_symbol_ts", "symbol", "snapshot_at"),
    )

    id              = Column(Integer, primary_key=True)
    symbol          = Column(String(20), nullable=False, index=True)
    source_name     = Column(String(100), nullable=False)
    snapshot_at     = Column(DateTime(timezone=True), nullable=False)
    ingested_at     = Column(DateTime(timezone=True), default=utcnow)
    freshness_tier  = Column(Enum(FreshnessTier), default=FreshnessTier.POLLED)

    price           = Column(Float)
    open            = Column(Float)
    high            = Column(Float)
    low             = Column(Float)
    volume          = Column(Float)
    change_pct      = Column(Float)
    confirmation_score = Column(Float)  # -100 to 100


# ─── Signal Scores ───────────────────────────────────────────────────────────

class SignalScore(Base):
    __tablename__ = "signal_scores"

    id                       = Column(Integer, primary_key=True)
    symbol                   = Column(String(20), nullable=False, index=True)
    scored_at                = Column(DateTime(timezone=True), default=utcnow, index=True)

    news_sentiment_score     = Column(Float, default=0.0)   # -100 to 100
    catalyst_score           = Column(Float, default=0.0)
    analyst_momentum_score   = Column(Float, default=0.0)
    insider_signal_score     = Column(Float, default=0.0)
    price_confirmation_score = Column(Float, default=0.0)
    total_trade_score        = Column(Float, default=0.0)   # weighted composite
    label                    = Column(Enum(SignalLabel), default=SignalLabel.NEUTRAL)

    # JSON explanation for "Why this stock?" panel
    explanation              = Column(JSONB)

    # Weights snapshot (what weights were used at scoring time)
    weights_snapshot         = Column(JSONB)


# ─── Alerts ──────────────────────────────────────────────────────────────────

class Alert(Base):
    __tablename__ = "alerts"

    id           = Column(Integer, primary_key=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol       = Column(String(20), nullable=False, index=True)
    alert_type   = Column(Enum(AlertType), nullable=False)
    channel      = Column(Enum(AlertChannel), default=AlertChannel.IN_APP)
    threshold    = Column(Float)   # e.g. score threshold
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime(timezone=True), default=utcnow)

    user         = relationship("User", back_populates="alerts")
    deliveries   = relationship("AlertDelivery", back_populates="alert", cascade="all, delete-orphan")


class AlertDelivery(Base):
    __tablename__ = "alert_deliveries"

    id           = Column(Integer, primary_key=True)
    alert_id     = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    delivered_at = Column(DateTime(timezone=True), default=utcnow)
    channel      = Column(Enum(AlertChannel), nullable=False)
    payload      = Column(JSONB)
    success      = Column(Boolean, default=True)
    error_msg    = Column(Text)

    alert        = relationship("Alert", back_populates="deliveries")


# ─── Provider Health ─────────────────────────────────────────────────────────

class ProviderHealth(Base):
    __tablename__ = "provider_health"

    id              = Column(Integer, primary_key=True)
    provider_name   = Column(String(100), unique=True, nullable=False, index=True)
    freshness_tier  = Column(Enum(FreshnessTier))
    is_enabled      = Column(Boolean, default=True)
    poll_interval_s = Column(Integer, default=60)
    last_sync_at    = Column(DateTime(timezone=True))
    last_event_at   = Column(DateTime(timezone=True))
    error_count     = Column(Integer, default=0)
    last_error      = Column(Text)
    status          = Column(String(50), default="unknown")  # healthy | degraded | down | unknown
    updated_at      = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ProviderSyncLog(Base):
    __tablename__ = "provider_sync_logs"

    id            = Column(Integer, primary_key=True)
    provider_name = Column(String(100), nullable=False, index=True)
    started_at    = Column(DateTime(timezone=True), default=utcnow)
    finished_at   = Column(DateTime(timezone=True))
    events_found  = Column(Integer, default=0)
    events_new    = Column(Integer, default=0)
    success       = Column(Boolean, default=True)
    error_msg     = Column(Text)


# ─── User Notes ──────────────────────────────────────────────────────────────

class UserNote(Base):
    __tablename__ = "user_notes"

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol     = Column(String(20), nullable=False, index=True)
    content    = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user       = relationship("User", back_populates="notes")

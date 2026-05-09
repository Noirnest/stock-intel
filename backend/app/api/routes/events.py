from datetime import datetime, timezone, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.models import NewsEvent, AnalystEvent, InsiderEvent
from app.api.routes.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()


class NewsEventOut(BaseModel):
    id: int
    symbol: str
    headline: Optional[str]
    summary: Optional[str]
    url: Optional[str]
    sentiment_score: Optional[float]
    freshness_tier: str
    event_timestamp: datetime
    source_name: str

    class Config:
        from_attributes = True


class AnalystEventOut(BaseModel):
    id: int
    symbol: str
    analyst_firm: Optional[str]
    analyst_name: Optional[str]
    action: Optional[str]
    from_rating: Optional[str]
    to_rating: Optional[str]
    from_target: Optional[float]
    to_target: Optional[float]
    momentum_score: Optional[float]
    freshness_tier: str
    event_timestamp: datetime
    source_name: str

    class Config:
        from_attributes = True


class InsiderEventOut(BaseModel):
    id: int
    symbol: str
    insider_name: Optional[str]
    insider_title: Optional[str]
    transaction_type: Optional[str]
    shares: Optional[float]
    price_per_share: Optional[float]
    total_value: Optional[float]
    signal_score: Optional[float]
    freshness_tier: str
    event_timestamp: datetime
    filing_date: Optional[datetime]
    transaction_date: Optional[datetime]
    source_name: str

    class Config:
        from_attributes = True


@router.get("/news", response_model=List[NewsEventOut])
async def get_news(
    symbol: Optional[str] = None,
    hours: int = Query(default=24, le=168),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    q = select(NewsEvent).where(NewsEvent.event_timestamp >= cutoff)
    if symbol:
        q = q.where(NewsEvent.symbol == symbol.upper())
    q = q.order_by(desc(NewsEvent.event_timestamp)).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/analyst", response_model=List[AnalystEventOut])
async def get_analyst(
    symbol: Optional[str] = None,
    hours: int = Query(default=72, le=720),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    q = select(AnalystEvent).where(AnalystEvent.event_timestamp >= cutoff)
    if symbol:
        q = q.where(AnalystEvent.symbol == symbol.upper())
    q = q.order_by(desc(AnalystEvent.event_timestamp)).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/insider", response_model=List[InsiderEventOut])
async def get_insider(
    symbol: Optional[str] = None,
    hours: int = Query(default=168, le=720),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    q = select(InsiderEvent).where(InsiderEvent.event_timestamp >= cutoff)
    if symbol:
        q = q.where(InsiderEvent.symbol == symbol.upper())
    q = q.order_by(desc(InsiderEvent.event_timestamp)).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()

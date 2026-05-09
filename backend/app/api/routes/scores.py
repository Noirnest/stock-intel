"""Scores API route."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.models.models import SignalScore
from app.api.routes.auth import get_current_user

router = APIRouter()


class SignalScoreOut(BaseModel):
    id: int
    symbol: str
    scored_at: datetime
    news_sentiment_score: float
    catalyst_score: float
    analyst_momentum_score: float
    insider_signal_score: float
    price_confirmation_score: float
    total_trade_score: float
    label: str
    explanation: Optional[list] = None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[SignalScoreOut])
async def get_scores(
    limit: int = Query(default=20, le=100),
    symbol: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Get latest signal scores, sorted by total_trade_score descending."""
    # Get the most recent score per symbol
    subq = (
        select(SignalScore.symbol, desc(SignalScore.scored_at).label("max_ts"))
        .group_by(SignalScore.symbol)
        .subquery()
    )
    q = (
        select(SignalScore)
        .join(subq, (SignalScore.symbol == subq.c.symbol))
        .order_by(desc(SignalScore.total_trade_score))
        .limit(limit)
    )
    if symbol:
        q = q.where(SignalScore.symbol == symbol.upper())

    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{symbol}", response_model=SignalScoreOut)
async def get_score_for_symbol(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(
        select(SignalScore)
        .where(SignalScore.symbol == symbol.upper())
        .order_by(desc(SignalScore.scored_at))
        .limit(1)
    )
    score = result.scalar_one_or_none()
    if not score:
        from fastapi import HTTPException
        raise HTTPException(404, detail=f"No score found for {symbol}")
    return score

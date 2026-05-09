"""Tickers API route."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional

from app.db.session import get_db
from app.models.models import StockSymbol
from app.api.routes.auth import get_current_user

router = APIRouter()


class TickerOut(BaseModel):
    symbol: str
    name: Optional[str]
    sector: Optional[str]
    industry: Optional[str]
    exchange: Optional[str]
    market_cap: Optional[float]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[TickerOut])
async def list_tickers(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(StockSymbol).where(StockSymbol.is_active == True))
    return result.scalars().all()


@router.get("/{symbol}", response_model=TickerOut)
async def get_ticker(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    from fastapi import HTTPException
    result = await db.execute(
        select(StockSymbol).where(StockSymbol.symbol == symbol.upper())
    )
    ticker = result.scalar_one_or_none()
    if not ticker:
        raise HTTPException(404, detail=f"Ticker {symbol} not found")
    return ticker

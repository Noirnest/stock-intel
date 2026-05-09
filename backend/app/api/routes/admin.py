"""Admin API routes — scoring weights, provider config."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional

from app.api.routes.auth import get_current_user, User
from app.scoring.engine import DEFAULT_WEIGHTS, PRESET_WEIGHTS, compute_score_for_symbol
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class WeightsPayload(BaseModel):
    news_sentiment: float = 0.20
    catalyst: float = 0.20
    analyst_momentum: float = 0.30
    insider_signal: float = 0.20
    price_confirmation: float = 0.10


class TestScoreRequest(BaseModel):
    symbol: str
    weights: Optional[WeightsPayload] = None


@router.get("/scoring/weights")
async def get_weights(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(403, detail="Admin only")
    return {
        "current": DEFAULT_WEIGHTS,
        "presets": PRESET_WEIGHTS,
    }


@router.post("/scoring/test")
async def test_score(
    req: TestScoreRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(403, detail="Admin only")

    weights = req.weights.model_dump() if req.weights else DEFAULT_WEIGHTS
    score = await compute_score_for_symbol(req.symbol, db, weights)
    return {
        "symbol": score.symbol,
        "total_trade_score": score.total_trade_score,
        "label": score.label,
        "components": {
            "news_sentiment_score": score.news_sentiment_score,
            "catalyst_score": score.catalyst_score,
            "analyst_momentum_score": score.analyst_momentum_score,
            "insider_signal_score": score.insider_signal_score,
            "price_confirmation_score": score.price_confirmation_score,
        },
        "explanation": score.explanation,
        "weights_used": weights,
    }

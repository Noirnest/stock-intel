"""
Signal Scoring Engine
─────────────────────
Computes a transparent, weighted composite score for each symbol.

Score dimensions (each -100 to 100):
  - news_sentiment_score     : NLP-based sentiment across recent headlines
  - catalyst_score           : event impact weighting (earnings, FDA, M&A, etc.)
  - analyst_momentum_score   : aggregate of recent analyst actions
  - insider_signal_score     : aggregate of recent insider transactions
  - price_confirmation_score : volume/momentum confirmation

Total trade score: weighted composite.
Labels: Strong Watch | Watch | Neutral | Avoid
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import json

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.models import (
    NewsEvent, AnalystEvent, InsiderEvent, PriceSnapshot,
    SignalScore, SignalLabel,
)

log = structlog.get_logger()

# ─── Default scoring weights (sum should = 1.0) ──────────────────────────────

DEFAULT_WEIGHTS = {
    "news_sentiment":     0.20,
    "catalyst":           0.20,
    "analyst_momentum":   0.30,
    "insider_signal":     0.20,
    "price_confirmation": 0.10,
}

PRESET_WEIGHTS = {
    "aggressive_scalp": {
        "news_sentiment":     0.35,
        "catalyst":           0.30,
        "analyst_momentum":   0.15,
        "insider_signal":     0.10,
        "price_confirmation": 0.10,
    },
    "catalyst_momentum": {
        "news_sentiment":     0.15,
        "catalyst":           0.35,
        "analyst_momentum":   0.30,
        "insider_signal":     0.15,
        "price_confirmation": 0.05,
    },
    "conservative": {
        "news_sentiment":     0.10,
        "catalyst":           0.15,
        "analyst_momentum":   0.40,
        "insider_signal":     0.30,
        "price_confirmation": 0.05,
    },
}

LOOKBACK_HOURS = 72  # How far back to consider events


def _label_from_score(score: float) -> SignalLabel:
    if score >= 50:
        return SignalLabel.STRONG_WATCH
    elif score >= 20:
        return SignalLabel.WATCH
    elif score >= -20:
        return SignalLabel.NEUTRAL
    else:
        return SignalLabel.AVOID


def _explain(
    symbol: str,
    scores: Dict[str, float],
    total: float,
    label: SignalLabel,
    weights: Dict[str, float],
) -> List[Dict[str, str]]:
    """Generate plain-English explanation bullets for the 'Why this stock?' panel."""
    explanations = []

    ns = scores.get("news_sentiment", 0)
    if ns >= 60:
        explanations.append({"type": "bullish", "text": f"Strong bullish news sentiment cluster ({ns:+.0f})"})
    elif ns >= 20:
        explanations.append({"type": "mild_bullish", "text": f"Mild positive news flow ({ns:+.0f})"})
    elif ns <= -60:
        explanations.append({"type": "bearish", "text": f"Bearish news sentiment cluster ({ns:+.0f})"})
    elif ns <= -20:
        explanations.append({"type": "mild_bearish", "text": f"Some negative news headwinds ({ns:+.0f})"})

    am = scores.get("analyst_momentum", 0)
    if am >= 50:
        explanations.append({"type": "bullish", "text": f"Bullish analyst momentum — recent upgrades or target raises ({am:+.0f})"})
    elif am <= -50:
        explanations.append({"type": "bearish", "text": f"Bearish analyst momentum — recent downgrades ({am:+.0f})"})

    ins = scores.get("insider_signal", 0)
    if ins >= 30:
        explanations.append({
            "type": "bullish",
            "text": f"Filing-delayed insider buy signal detected ({ins:+.0f}) — note: filing date may lag transaction by several days"
        })
    elif ins <= -30:
        explanations.append({
            "type": "bearish",
            "text": f"Filing-delayed insider sell signal detected ({ins:+.0f}) — note: filing date may lag transaction by several days"
        })

    cs = scores.get("catalyst", 0)
    if abs(cs) < 10:
        explanations.append({"type": "neutral", "text": "No major catalyst detected in recent event window"})

    pc = scores.get("price_confirmation", 0)
    if pc >= 30:
        explanations.append({"type": "bullish", "text": f"Price/volume confirmation of bullish thesis ({pc:+.0f})"})
    elif pc <= -30:
        explanations.append({"type": "bearish", "text": f"Price action does not confirm signal — high-volatility setup"})

    if not explanations:
        explanations.append({"type": "neutral", "text": "Low-confidence signal — insufficient signal data in the lookback window"})

    return explanations


async def compute_score_for_symbol(
    symbol: str,
    session: AsyncSession,
    weights: Optional[Dict[str, float]] = None,
) -> SignalScore:
    """Compute and persist signal score for a single symbol."""
    weights = weights or DEFAULT_WEIGHTS
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)

    # ── News sentiment ────────────────────────────────────────────────────────
    news_result = await session.execute(
        select(NewsEvent)
        .where(NewsEvent.symbol == symbol, NewsEvent.event_timestamp >= cutoff)
        .order_by(desc(NewsEvent.event_timestamp))
        .limit(20)
    )
    news_events = news_result.scalars().all()

    if news_events:
        sentiments = [n.sentiment_score or 0 for n in news_events]
        # Recency-weighted average (more recent = higher weight)
        total_w = 0
        weighted_sum = 0
        for i, s in enumerate(sentiments):
            w = 1 / (i + 1)  # 1, 0.5, 0.33, ...
            weighted_sum += s * w
            total_w += w
        news_sentiment_score = round(weighted_sum / total_w, 1) if total_w > 0 else 0.0
    else:
        news_sentiment_score = 0.0

    # ── Catalyst score (derived from news magnitude) ──────────────────────────
    # For v1: high-magnitude sentiment events indicate catalysts
    if news_events:
        high_magnitude = [n for n in news_events if abs(n.sentiment_score or 0) >= 60]
        catalyst_score = round(
            sum((n.sentiment_score or 0) for n in high_magnitude) / max(len(high_magnitude), 1),
            1
        ) if high_magnitude else 0.0
    else:
        catalyst_score = 0.0

    # ── Analyst momentum ──────────────────────────────────────────────────────
    analyst_result = await session.execute(
        select(AnalystEvent)
        .where(AnalystEvent.symbol == symbol, AnalystEvent.event_timestamp >= cutoff)
        .order_by(desc(AnalystEvent.event_timestamp))
        .limit(10)
    )
    analyst_events = analyst_result.scalars().all()

    if analyst_events:
        scores_a = [a.momentum_score or 0 for a in analyst_events]
        analyst_momentum_score = round(sum(scores_a) / len(scores_a), 1)
    else:
        analyst_momentum_score = 0.0

    # ── Insider signal ────────────────────────────────────────────────────────
    insider_result = await session.execute(
        select(InsiderEvent)
        .where(InsiderEvent.symbol == symbol, InsiderEvent.event_timestamp >= cutoff)
        .order_by(desc(InsiderEvent.event_timestamp))
        .limit(5)
    )
    insider_events = insider_result.scalars().all()

    if insider_events:
        scores_i = [i.signal_score or 0 for i in insider_events]
        insider_signal_score = round(sum(scores_i) / len(scores_i), 1)
    else:
        insider_signal_score = 0.0

    # ── Price confirmation ────────────────────────────────────────────────────
    price_result = await session.execute(
        select(PriceSnapshot)
        .where(PriceSnapshot.symbol == symbol)
        .order_by(desc(PriceSnapshot.snapshot_at))
        .limit(1)
    )
    price_snap = price_result.scalar_one_or_none()
    price_confirmation_score = price_snap.confirmation_score if price_snap else 0.0

    # ── Weighted composite ────────────────────────────────────────────────────
    component_scores = {
        "news_sentiment":     news_sentiment_score,
        "catalyst":           catalyst_score,
        "analyst_momentum":   analyst_momentum_score,
        "insider_signal":     insider_signal_score,
        "price_confirmation": price_confirmation_score or 0.0,
    }

    total_trade_score = round(
        sum(component_scores[k] * weights[k] for k in weights),
        1,
    )
    total_trade_score = max(-100, min(100, total_trade_score))
    label = _label_from_score(total_trade_score)
    explanation = _explain(symbol, component_scores, total_trade_score, label, weights)

    score_row = SignalScore(
        symbol=symbol,
        scored_at=datetime.now(timezone.utc),
        news_sentiment_score=news_sentiment_score,
        catalyst_score=catalyst_score,
        analyst_momentum_score=analyst_momentum_score,
        insider_signal_score=insider_signal_score,
        price_confirmation_score=price_confirmation_score or 0.0,
        total_trade_score=total_trade_score,
        label=label,
        explanation=explanation,
        weights_snapshot=weights,
    )
    session.add(score_row)
    await session.commit()
    await session.refresh(score_row)

    log.info(
        "scoring.computed",
        symbol=symbol,
        total=total_trade_score,
        label=label,
    )
    return score_row


async def compute_scores_for_all(
    session: AsyncSession,
    symbols: List[str],
    weights: Optional[Dict[str, float]] = None,
) -> List[SignalScore]:
    results = []
    for symbol in symbols:
        try:
            score = await compute_score_for_symbol(symbol, session, weights)
            results.append(score)
        except Exception as e:
            log.error("scoring.failed", symbol=symbol, error=str(e))
    return results

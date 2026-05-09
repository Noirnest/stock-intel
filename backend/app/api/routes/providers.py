"""Providers health and config API route."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.models.models import ProviderHealth
from app.api.routes.auth import get_current_user

router = APIRouter()


class ProviderHealthOut(BaseModel):
    id: int
    provider_name: str
    freshness_tier: Optional[str]
    is_enabled: bool
    poll_interval_s: int
    last_sync_at: Optional[datetime]
    last_event_at: Optional[datetime]
    error_count: int
    last_error: Optional[str]
    status: str

    class Config:
        from_attributes = True


class ProviderUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    poll_interval_s: Optional[int] = None


@router.get("/", response_model=List[ProviderHealthOut])
async def list_providers(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(ProviderHealth))
    return result.scalars().all()


@router.patch("/{provider_name}", response_model=ProviderHealthOut)
async def update_provider(
    provider_name: str,
    update: ProviderUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    from fastapi import HTTPException
    result = await db.execute(
        select(ProviderHealth).where(ProviderHealth.provider_name == provider_name)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(404, detail=f"Provider {provider_name} not found")

    if update.is_enabled is not None:
        provider.is_enabled = update.is_enabled
    if update.poll_interval_s is not None:
        provider.poll_interval_s = update.poll_interval_s

    await db.commit()
    await db.refresh(provider)
    return provider

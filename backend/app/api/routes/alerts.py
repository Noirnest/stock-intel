"""Alerts API stub."""
from fastapi import APIRouter, Depends
from app.api.routes.auth import get_current_user

router = APIRouter()


@router.get("/")
async def list_alerts(_=Depends(get_current_user)):
    # TODO: implement full alerts CRUD
    return []


@router.post("/")
async def create_alert(_=Depends(get_current_user)):
    # TODO: implement alert creation with webhook/email delivery
    return {"detail": "Not yet implemented"}

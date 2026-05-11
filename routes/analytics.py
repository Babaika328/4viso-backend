from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from middleware.auth import require_user
from models.user import User
from schemas.analytics import (
    SummaryOut,
    RiskDistributionOut,
    ModeBreakdownOut,
)
import services.analytics as svc

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary", response_model=SummaryOut)
async def summary(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_user),
):
    return await svc.get_summary(db)


@router.get("/risk", response_model=RiskDistributionOut)
async def risk_distribution(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_user),
):
    return await svc.get_risk_distribution(db)


@router.get("/modes", response_model=ModeBreakdownOut)
async def mode_breakdown(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_user),
):
    return await svc.get_mode_breakdown(db)


@router.get("/cargo")
async def cargo_breakdown(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_user),
):
    return await svc.get_cargo_breakdown(db)


@router.get("/caretakers")
async def caretaker_breakdown(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_user),
):
    return await svc.get_caretaker_breakdown(db)
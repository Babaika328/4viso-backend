from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from middleware.auth import require_admin
from models.user import User, UserRole
from schemas.user import UserOut, UserRoleUpdate, UserActiveUpdate, AccessLogOut
import services.admin as svc

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── Users ─────────────────────────────────────────────────

@router.get("/users", response_model=list[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await svc.get_all_users(db)

@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await svc.get_user_by_id(db, user_id)

@router.patch("/users/{user_id}/role", response_model=UserOut)
async def update_role(
    user_id: int,
    data: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await svc.update_user_role(db, user_id, data.role)

@router.patch("/users/{user_id}/activate", response_model=UserOut)
async def set_active(
    user_id: int,
    data: UserActiveUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await svc.toggle_user_active(db, user_id, data.is_active)

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await svc.delete_user(db, user_id)
    return {"detail": "User deleted"}


# ── Access logs ───────────────────────────────────────────

@router.get("/logs", response_model=list[AccessLogOut])
async def get_logs(
    user_id: int | None = Query(None),
    action:  str | None = Query(None),
    limit:   int        = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await svc.get_all_logs(db, user_id=user_id, action=action, limit=limit)
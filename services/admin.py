from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException
from models.user import User, UserRole, AccessLog, RefreshToken
from schemas.user import UserCreate, UserLogin, PasswordChange, AccountUpdate
from datetime import datetime


# ── Users ─────────────────────────────────────────────────

async def get_all_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()

async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def update_user_role(db: AsyncSession, user_id: int, role: UserRole) -> User:
    user = await get_user_by_id(db, user_id)
    user.role = role
    await db.commit()
    await db.refresh(user)
    return user

async def toggle_user_active(db: AsyncSession, user_id: int, is_active: bool) -> User:
    user = await get_user_by_id(db, user_id)
    user.is_active = is_active
    await db.commit()
    await db.refresh(user)
    return user

async def delete_user(db: AsyncSession, user_id: int):
    user = await get_user_by_id(db, user_id)
    await db.delete(user)
    await db.commit()


# ── Access logs ───────────────────────────────────────────

async def get_all_logs(
    db: AsyncSession,
    user_id:    int | None      = None,
    action:     str | None      = None,
    date_from:  datetime | None = None,
    date_to:    datetime | None = None,
    limit:      int             = 100,
) -> list[AccessLog]:
    query = select(AccessLog).order_by(AccessLog.timestamp.desc()).limit(limit)
    if user_id:
        query = query.where(AccessLog.user_id == user_id)
    if action:
        query = query.where(AccessLog.action == action)
    if date_from:
        query = query.where(AccessLog.timestamp >= date_from)
    if date_to:
        query = query.where(AccessLog.timestamp <= date_to)
    result = await db.execute(query)
    return result.scalars().all()

async def revoke_all_user_tokens(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,
        )
    )
    tokens = result.scalars().all()
    for t in tokens:
        t.revoked = True
    await db.commit()
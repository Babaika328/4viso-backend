from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from slowapi import Limiter
from slowapi.util import get_remote_address
from database import get_db
from schemas.user import (
    UserCreate,
    UserLogin,
    UserOut,
    TokenOut,
    PasswordChange,
    AccountUpdate,
    RefreshRequest,
)
from services.auth import (
    register_user,
    login_user,
    create_token,
    create_refresh_token,
    store_refresh_token,
    revoke_refresh_token,
    validate_refresh_token,
    decode_refresh_token,
    change_password,
    update_account,
)
from middleware.auth import get_current_user
from models.user import User

router  = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


# ── Register ──────────────────────────────────────────────

@router.post("/register", response_model=TokenOut)
@limiter.limit("10/minute")
async def register(
    request: Request,
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    ip            = request.client.host if request.client else None
    user          = await register_user(db, data, ip)
    access_token  = create_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)
    await store_refresh_token(db, user.id, refresh_token)
    return TokenOut(
        access_token  = access_token,
        refresh_token = refresh_token,
        user          = UserOut.model_validate(user)
    )


# ── Login ─────────────────────────────────────────────────

@router.post("/login", response_model=TokenOut)
@limiter.limit("20/minute")
async def login(
    request: Request,
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    ip            = request.client.host if request.client else None
    user          = await login_user(db, data.email, data.password, ip)
    access_token  = create_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)
    await store_refresh_token(db, user.id, refresh_token)
    return TokenOut(
        access_token  = access_token,
        refresh_token = refresh_token,
        user          = UserOut.model_validate(user)
    )


# ── Refresh ───────────────────────────────────────────────

@router.post("/refresh", response_model=TokenOut)
@limiter.limit("30/minute")
async def refresh(
    request: Request,
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    await validate_refresh_token(db, data.refresh_token)

    payload = decode_refresh_token(data.refresh_token)
    user_id = int(payload.get("sub"))

    result = await db.execute(select(User).where(User.id == user_id))
    user   = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled"
        )

    # rotate — revoke old, issue new
    await revoke_refresh_token(db, data.refresh_token)
    new_refresh = create_refresh_token(user.id)
    await store_refresh_token(db, user.id, new_refresh)

    return TokenOut(
        access_token  = create_token(user.id, user.role),
        refresh_token = new_refresh,
        user          = UserOut.model_validate(user)
    )


# ── Logout ────────────────────────────────────────────────

@router.post("/logout")
async def logout(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await revoke_refresh_token(db, data.refresh_token)
    return {"detail": "Logged out successfully"}


# ── Me ────────────────────────────────────────────────────

@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


# ── Update account ────────────────────────────────────────

@router.patch("/me", response_model=UserOut)
async def update_me(
    data: AccountUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await update_account(db, current_user, data.organisation)


# ── Change password ───────────────────────────────────────

@router.post("/change-password", response_model=UserOut)
async def change_pwd(
    data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await change_password(db, current_user, data.current_password, data.new_password)
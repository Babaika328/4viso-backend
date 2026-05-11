from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from schemas.user import UserCreate, UserLogin, UserOut, TokenOut, PasswordChange, AccountUpdate
from services.auth import register_user, login_user, create_token, change_password, update_account
from middleware.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenOut)
async def register(
    data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    ip = request.client.host if request.client else None
    user = await register_user(db, data, ip)
    token = create_token(user.id, user.role)
    return TokenOut(
        access_token=token,
        user=UserOut.model_validate(user)
    )

@router.post("/login", response_model=TokenOut)
async def login(
    data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    ip = request.client.host if request.client else None
    user = await login_user(db, data.email, data.password, ip)
    token = create_token(user.id, user.role)
    return TokenOut(
        access_token=token,
        user=UserOut.model_validate(user)
    )

@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)

@router.post("/change-password", response_model=UserOut)
async def change_pwd(
    data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await change_password(db, current_user, data.current_password, data.new_password)

@router.patch("/me", response_model=UserOut)
async def update_me(
    data: AccountUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await update_account(db, current_user, data.organisation)
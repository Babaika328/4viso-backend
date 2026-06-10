import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status
from models.user import User, AccessLog, UserRole, RefreshToken
from schemas.user import UserCreate
import os

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── JWT config ────────────────────────────────────────────

SECRET_KEY             = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY not found in environment")
ALGORITHM              = "HS256"
TOKEN_EXPIRE_MINUTES   = 60 * 8    # 8 hours
REFRESH_TOKEN_EXPIRE_DAYS = 30


# ── Access token ──────────────────────────────────────────

def create_token(user_id: int, role: UserRole) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub":  str(user_id),
        "role": role.value,
        "exp":  expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalid or expired"
        )


# ── Refresh token ─────────────────────────────────────────

def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub":  str(user_id),
        "type": "refresh",
        "exp":  expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalid or expired"
        )

async def store_refresh_token(db: AsyncSession, user_id: int, token: str):
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    rt = RefreshToken(
        user_id    = user_id,
        token      = token,
        expires_at = expire,
    )
    db.add(rt)
    await db.commit()

async def revoke_refresh_token(db: AsyncSession, token: str):
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == token)
    )
    rt = result.scalar_one_or_none()
    if rt:
        rt.revoked = True
        await db.commit()

async def validate_refresh_token(db: AsyncSession, token: str) -> RefreshToken:
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == token)
    )
    rt = result.scalar_one_or_none()

    if not rt:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    if rt.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked"
        )
    if rt.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired"
        )
    return rt


# ── User helpers ──────────────────────────────────────────

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def write_access_log(db: AsyncSession, user_id: int, action: str, ip: str | None):
    log = AccessLog(user_id=user_id, action=action, ip_address=ip)
    db.add(log)
    await db.commit()


# ── Register ──────────────────────────────────────────────

async def register_user(db: AsyncSession, data: UserCreate, ip: str | None) -> User:
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user = User(
        email           = data.email,
        hashed_password = hash_password(data.password),
        role            = UserRole.user,   # self-registration is always 'user'; admins assign elevated roles
        organisation    = data.organisation,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    await write_access_log(db, user.id, "register", ip)
    return user


# ── Login ─────────────────────────────────────────────────

async def login_user(db: AsyncSession, email: str, password: str, ip: str | None) -> User:
    user = await get_user_by_email(db, email)

    if not user or not verify_password(password, user.hashed_password):
        if user:
            await write_access_log(db, user.id, "failed_login", ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    await db.execute(
        update(User).where(User.id == user.id).values(
            last_login=datetime.now(timezone.utc)
        )
    )
    await db.commit()
    await db.refresh(user)
    await write_access_log(db, user.id, "login", ip)
    return user


# ── Change password ───────────────────────────────────────

async def change_password(db: AsyncSession, user: User, current: str, new: str) -> User:
    if not verify_password(current, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    user.hashed_password = hash_password(new)
    await db.commit()
    await db.refresh(user)
    return user


# ── Update account ────────────────────────────────────────

async def update_account(db: AsyncSession, user: User, organisation: str | None) -> User:
    user.organisation = organisation
    await db.commit()
    await db.refresh(user)
    return user
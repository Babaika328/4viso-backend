from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.user import User, UserRole
from services.auth import decode_token

bearer_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    payload = decode_token(credentials.credentials)
    user_id = int(payload.get("sub"))

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled"
        )
    return user

def require_role(*roles: UserRole):
    async def guard(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied for role: {current_user.role.value}"
            )
        return current_user
    return guard

require_admin   = require_role(UserRole.admin)
require_auditor = require_role(UserRole.auditor, UserRole.admin)
require_staff   = require_role(UserRole.staff, UserRole.admin)
require_port    = require_role(UserRole.port, UserRole.admin)
require_user    = require_role(UserRole.user, UserRole.staff, UserRole.auditor, UserRole.admin)
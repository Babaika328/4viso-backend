from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from models.user import UserRole
import re

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.user
    organisation: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/`~';]", v):
            raise ValueError("Password must contain at least one special character")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    organisation: str | None
    last_login: datetime | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

# ── Token response after login/register ───────────────────
class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
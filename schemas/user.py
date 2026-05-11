from pydantic import BaseModel, EmailStr, field_validator, Field
from datetime import datetime
from models.user import UserRole
import re


class UserCreate(BaseModel):
    email:        EmailStr
    password:     str = Field(..., min_length=8, max_length=100)
    role:         UserRole = UserRole.user
    organisation: str | None = Field(None, max_length=200)

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
    email:    EmailStr
    password: str = Field(..., max_length=100)


class UserOut(BaseModel):
    id:           int
    email:        EmailStr
    role:         UserRole
    organisation: str | None
    last_login:   datetime | None
    is_active:    bool
    created_at:   datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    user:          UserOut


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordChange(BaseModel):
    current_password: str = Field(..., max_length=100)
    new_password:     str = Field(..., max_length=100)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Must contain uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Must contain lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Must contain a number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/`~';]", v):
            raise ValueError("Must contain a special character")
        return v


class AccountUpdate(BaseModel):
    organisation: str | None = Field(None, max_length=200)


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserActiveUpdate(BaseModel):
    is_active: bool


class AccessLogOut(BaseModel):
    id:         int
    user_id:    int
    action:     str
    ip_address: str | None
    timestamp:  datetime

    model_config = {"from_attributes": True}
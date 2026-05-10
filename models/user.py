from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime, timezone
import enum

class Base(DeclarativeBase):
    pass

class UserRole(str, enum.Enum):
    admin = "admin"
    auditor = "auditor"
    staff = "staff"
    port = "port"
    user = "user"

class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role            = Column(Enum(UserRole), nullable=False, default=UserRole.user)
    organisation    = Column(String, nullable=True)
    do_not_share    = Column(Boolean, default=True)   # GDPR flag
    last_login      = Column(DateTime(timezone=True), nullable=True)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    access_logs     = relationship("AccessLog", back_populates="user")


class AccessLog(Base):
    __tablename__ = "access_logs"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    action     = Column(String, nullable=False)   # e.g. "login", "logout", "failed_login"
    ip_address = Column(String, nullable=True)
    timestamp  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user       = relationship("User", back_populates="access_logs")
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.auth import Organization, User, ApiKey
from app.models.supporting import Session

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, org_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "org": org_id,
        "roles": role,
        "iat": datetime.now(timezone.utc),
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str, org_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_REFRESH_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "org": org_id,
        "roles": role,
        "iat": datetime.now(timezone.utc),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except Exception:
        return None


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generate_api_key() -> tuple[str, str, str]:
    raw = "urja_" + secrets.token_hex(32)
    prefix = raw[:12]
    key_hash = hashlib.sha256(raw.encode()).hexdigest()
    return raw, prefix, key_hash


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user


async def create_session(
    db: AsyncSession, user: User, refresh_token: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None
) -> Session:
    token_hash = hash_refresh_token(refresh_token)
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_REFRESH_EXPIRE_MINUTES)
    session = Session(
        user_id=user.id,
        organization_id=user.organization_id,
        refresh_token_hash=token_hash,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=expire,
    )
    db.add(session)
    await db.flush()
    return session


async def revoke_session(db: AsyncSession, refresh_token: str) -> bool:
    token_hash = hash_refresh_token(refresh_token)
    result = await db.execute(
        select(Session).where(Session.refresh_token_hash == token_hash, Session.is_revoked == False)
    )
    session = result.scalar_one_or_none()
    if session is None:
        return False
    session.is_revoked = True
    await db.flush()
    return True


async def rotate_session(
    db: AsyncSession, old_refresh_token: str, new_refresh_token: str
) -> bool:
    token_hash = hash_refresh_token(old_refresh_token)
    result = await db.execute(
        select(Session).where(
            Session.refresh_token_hash == token_hash,
            Session.is_revoked == False,
            Session.expires_at > datetime.now(timezone.utc),
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        return False
    session.is_revoked = True
    new_hash = hash_refresh_token(new_refresh_token)
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_REFRESH_EXPIRE_MINUTES)
    new_session = Session(
        user_id=session.user_id,
        organization_id=session.organization_id,
        refresh_token_hash=new_hash,
        ip_address=session.ip_address,
        user_agent=session.user_agent,
        expires_at=expire,
    )
    db.add(new_session)
    await db.flush()
    return True


async def get_api_keys(db: AsyncSession, org_id: str) -> list[ApiKey]:
    result = await db.execute(
        select(ApiKey).where(ApiKey.organization_id == org_id).order_by(ApiKey.created_at.desc())
    )
    return list(result.scalars().all())

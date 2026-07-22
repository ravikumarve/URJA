from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.auth import Organization, User, ApiKey
from app.models.enums import UserRole
from app.schemas.auth import (
    LoginRequest, RegisterRequest, RefreshRequest, LogoutRequest,
    TokenData, UserResponse, UserMinimal, InviteUserRequest, ChangeRoleRequest,
    RegisterResponse, LoginResponse, ApiKeyResponse, ApiKeyCreateRequest,
    ApiKeyCreateResponse, MessageResponse,
)
from app.services.auth import (
    authenticate_user, hash_password, create_access_token, create_refresh_token,
    decode_token, generate_api_key, create_session, revoke_session,
    rotate_session, get_api_keys,
)

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    existing_org = await db.execute(
        select(Organization).where(Organization.slug == body.organization_slug)
    )
    if existing_org.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Organization slug already exists")

    existing_user = await db.execute(select(User).where(User.email == body.email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    org = Organization(
        name=body.organization_name,
        slug=body.organization_slug,
        timezone=body.timezone,
        currency=body.currency,
    )
    db.add(org)
    await db.flush()

    user = User(
        organization_id=org.id,
        email=body.email,
        password_hash=hash_password(body.password),
        display_name=body.display_name,
        role="admin",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    access_token = create_access_token(str(user.id), str(org.id), user.role)
    refresh_token = create_refresh_token(str(user.id), str(org.id), user.role)
    await create_session(
        db, user, refresh_token,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return {
        "organization": {
            "id": str(org.id),
            "name": org.name,
            "slug": org.slug,
            "timezone": org.timezone,
            "currency": org.currency,
        },
        "user": {
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
        },
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 900,
    }


@router.post("/login")
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, body.email, body.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    user.last_login_at = func.now()
    await db.flush()

    access_token = create_access_token(str(user.id), str(user.organization_id), user.role)
    refresh_token = create_refresh_token(str(user.id), str(user.organization_id), user.role)
    await create_session(
        db, user, refresh_token,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
            "organization_id": str(user.organization_id),
            "is_active": user.is_active,
            "last_login_at": user.last_login_at,
            "created_at": user.created_at,
        },
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 900,
    }


@router.post("/refresh")
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = payload.get("sub")
    org_id = payload.get("org")
    role = payload.get("roles")

    if not user_id or not org_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    new_access = create_access_token(str(user.id), str(user.organization_id), user.role)
    new_refresh = create_refresh_token(str(user.id), str(user.organization_id), user.role)

    await rotate_session(db, body.refresh_token, new_refresh)

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": 900,
    }


@router.post("/logout")
async def logout(body: LogoutRequest, db: AsyncSession = Depends(get_db)):
    await revoke_session(db, body.refresh_token)
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        display_name=current_user.display_name,
        role=current_user.role,
        is_active=current_user.is_active,
        organization_id=str(current_user.organization_id),
        last_login_at=current_user.last_login_at,
        created_at=current_user.created_at,
    )


@router.post("/api-keys", status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: ApiKeyCreateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(ApiKey).where(ApiKey.organization_id == current_user.organization_id, ApiKey.name == body.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="API key name already exists")

    raw_key, prefix, key_hash = generate_api_key()
    api_key = ApiKey(
        organization_id=current_user.organization_id,
        key_prefix=prefix,
        key_hash=key_hash,
        name=body.name,
        scope=body.scope,
        expires_at=body.expires_at,
    )
    db.add(api_key)
    await db.flush()
    await db.refresh(api_key)

    return ApiKeyCreateResponse(
        id=str(api_key.id),
        key_prefix=api_key.key_prefix,
        full_key=raw_key,
        name=api_key.name,
        scope=api_key.scope,
        expires_at=api_key.expires_at,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
    )


@router.get("/api-keys")
async def list_api_keys(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    keys = await get_api_keys(db, str(current_user.organization_id))
    return [
        ApiKeyResponse(
            id=str(k.id),
            key_prefix=k.key_prefix,
            name=k.name,
            scope=k.scope,
            expires_at=k.expires_at,
            last_used_at=k.last_used_at,
            is_active=k.is_active,
            created_at=k.created_at,
        )
        for k in keys
    ]


@router.delete("/api-keys/{api_key_id}")
async def revoke_api_key(
    api_key_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == api_key_id,
            ApiKey.organization_id == current_user.organization_id,
        )
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    api_key.is_active = False
    await db.flush()
    return {"message": "API key revoked successfully"}


@router.get("/users")
async def list_users(
    page: int = 1,
    page_size: int = 20,
    role: str | None = None,
    status_filter: str | None = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(User).where(User.organization_id == current_user.organization_id)
    count_query = select(func.count(User.id)).where(User.organization_id == current_user.organization_id)

    if role:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)
    if status_filter == "active":
        query = query.where(User.is_active == True)
        count_query = count_query.where(User.is_active == True)
    elif status_filter == "inactive":
        query = query.where(User.is_active == False)
        count_query = count_query.where(User.is_active == False)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(User.created_at.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "items": [
            UserMinimal(
                id=str(u.id),
                email=u.email,
                display_name=u.display_name,
                role=u.role,
                is_active=u.is_active,
                last_login_at=u.last_login_at,
                created_at=u.created_at,
            )
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/users/invite", status_code=status.HTTP_201_CREATED)
async def invite_user(
    body: InviteUserRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(User).where(
            User.organization_id == current_user.organization_id,
            User.email == body.email,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists in the organization")

    temp_password = "changeme123"
    user = User(
        organization_id=current_user.organization_id,
        email=body.email,
        password_hash=hash_password(temp_password),
        display_name=body.display_name,
        role=body.role.value,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    return UserMinimal(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.put("/users/{user_id}/role")
async def change_user_role(
    user_id: str,
    body: ChangeRoleRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if user_id == str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change your own role")

    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.organization_id == current_user.organization_id,
        )
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.role = body.role.value
    await db.flush()
    await db.refresh(user)

    return UserMinimal(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )


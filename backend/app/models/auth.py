import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint, Text, Numeric, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    name = Column(Text, nullable=False)
    slug = Column(Text, nullable=False, unique=True)
    logo_url = Column(Text)
    timezone = Column(Text, nullable=False, default="UTC", server_default=func.now())  
    currency = Column(Text, nullable=False, default="USD")
    emission_factor = Column(Numeric(8, 4), nullable=False, default=0.92)
    is_active = Column(Boolean, nullable=False, default=True, server_default=func.now())
    extra_metadata = Column("metadata", JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    users = relationship("User", back_populates="organization", lazy="selectin")
    api_keys = relationship("ApiKey", back_populates="organization", lazy="selectin")
    asset_sites = relationship("AssetSite", back_populates="organization", lazy="selectin")
    assets = relationship("Asset", back_populates="organization", lazy="selectin")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(Text, nullable=False)
    password_hash = Column(Text, nullable=False)
    display_name = Column(Text, nullable=False)
    role = Column(String(16), nullable=False, default="viewer")
    is_active = Column(Boolean, nullable=False, default=True)
    email_verified_at = Column(DateTime(timezone=True))
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    organization = relationship("Organization", back_populates="users", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("organization_id", "email", name="uq_users_org_email"),
    )


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    key_prefix = Column(Text, nullable=False)
    key_hash = Column(Text, nullable=False, unique=True)
    name = Column(Text, nullable=False)
    scope = Column(String(8), nullable=False, default="read")
    expires_at = Column(DateTime(timezone=True))
    last_used_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    organization = relationship("Organization", back_populates="api_keys", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_api_keys_name_org"),
    )

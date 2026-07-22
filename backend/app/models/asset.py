import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint, Text, Numeric, Date, SmallInteger, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class AssetSite(Base):
    __tablename__ = "asset_sites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(Text, nullable=False)
    code = Column(Text, nullable=False)
    description = Column(Text)
    address = Column(Text)
    latitude = Column(Numeric(10, 7))
    longitude = Column(Numeric(10, 7))
    capacity_mw = Column(Numeric(10, 4), nullable=False)
    timezone = Column(Text, nullable=False, default="UTC")
    status = Column(String(20), nullable=False, default="active")
    extra_metadata = Column("metadata", JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    organization = relationship("Organization", back_populates="asset_sites", lazy="selectin")
    assets = relationship("Asset", back_populates="site", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_asset_sites_org_code"),
    )


class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    site_id = Column(UUID(as_uuid=True), ForeignKey("asset_sites.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL"), index=True)
    asset_type = Column(String(20), nullable=False)
    name = Column(Text, nullable=False)
    code = Column(Text, nullable=False)
    serial_number = Column(Text)
    manufacturer = Column(Text)
    model = Column(Text)
    capacity_kw = Column(Numeric(12, 4))
    latitude = Column(Numeric(10, 7))
    longitude = Column(Numeric(10, 7))
    commissioning_date = Column(Date)
    status = Column(String(16), nullable=False, default="active")
    health_score = Column(Numeric(5, 2), default=100.00)
    config = Column(JSONB, default=dict)
    extra_metadata = Column("metadata", JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    organization = relationship("Organization", back_populates="assets", lazy="selectin")
    site = relationship("AssetSite", back_populates="assets", lazy="selectin")
    parent = relationship("Asset", remote_side="Asset.id", back_populates="children", lazy="selectin")
    children = relationship("Asset", back_populates="parent", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_assets_org_code"),
    )


class AssetRelationship(Base):
    __tablename__ = "asset_relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    child_asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(String(20), nullable=False, default="contains")
    position_index = Column(SmallInteger)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
    extra_metadata = Column("metadata", JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("parent_asset_id", "child_asset_id", "relationship_type", "ended_at", name="uq_asset_relationships_pair"),
    )

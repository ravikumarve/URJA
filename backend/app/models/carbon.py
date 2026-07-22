import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Numeric, func, PrimaryKeyConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class CarbonCredit(Base):
    __tablename__ = "carbon_credits"

    ts = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    credit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(String(12), nullable=False, default="pending")
    quantity = Column(Numeric(14, 4), nullable=False)
    unit = Column(Text, nullable=False, default="tCO2e")
    methodology = Column(Text, nullable=False, default="IPMVP_v2.1")
    generation_start = Column(DateTime(timezone=True), nullable=False)
    generation_end = Column(DateTime(timezone=True), nullable=False)
    total_kwh = Column(Numeric(14, 4), nullable=False)
    emission_factor = Column(Numeric(8, 4), nullable=False)
    registry_tx_id = Column(Text)
    registry_url = Column(Text)
    issued_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    retired_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    extra_metadata = Column("metadata", JSONB, default=dict)

    __table_args__ = (
        PrimaryKeyConstraint("ts", "credit_id"),
        CheckConstraint("generation_end > generation_start", name="ck_carbon_generation_range"),
        {
            "timescaledb_hypertable": {
                "time_column": "ts",
            }
        },
    )

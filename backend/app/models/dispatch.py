import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Numeric, Integer, func, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class CurtailmentEvent(Base):
    __tablename__ = "curtailment_events"

    ts = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    duration_minutes = Column(Integer, nullable=False)
    expected_kwh = Column(Numeric(14, 4), nullable=False)
    actual_kwh = Column(Numeric(14, 4), nullable=False)
    curtailed_kwh = Column(Numeric(14, 4), nullable=False)
    price_per_kwh = Column(Numeric(8, 4), nullable=False)
    revenue_lost = Column(Numeric(14, 4), nullable=False)
    grid_price_source = Column(Text)
    is_resolved = Column(Boolean, nullable=False, default=False)
    resolved_at = Column(DateTime(timezone=True))

    __table_args__ = (
        PrimaryKeyConstraint("ts", "event_id"),
        {
            "timescaledb_hypertable": {
                "time_column": "ts",
            }
        },
    )


class DispatchRule(Base):
    __tablename__ = "dispatch_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=100)
    condition_type = Column(String(24), nullable=False)
    condition_config = Column(JSONB, nullable=False, default=dict)
    action = Column(String(22), nullable=False)
    action_config = Column(JSONB, default=dict)
    target_asset_type = Column(String(20))
    cooldown_minutes = Column(Integer, nullable=False, default=15)
    last_triggered_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class DispatchDecision(Base):
    __tablename__ = "dispatch_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("dispatch_rules.id", ondelete="SET NULL"), index=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    curtailment_event_id = Column(UUID(as_uuid=True), ForeignKey("curtailment_events.event_id", ondelete="SET NULL"), index=True)
    status = Column(String(12), nullable=False, default="pending")
    action_taken = Column(String(22), nullable=False)
    action_params = Column(JSONB, default=dict)
    triggered_value = Column(Numeric(14, 4))
    expected_outcome = Column(Numeric(14, 4))
    actual_outcome = Column(Numeric(14, 4))
    failure_reason = Column(Text)
    executed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    rule = relationship("DispatchRule", lazy="selectin")

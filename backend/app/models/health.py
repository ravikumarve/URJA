import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Numeric, func, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.database import Base


class HealthMetric(Base):
    __tablename__ = "health_metrics"

    ts = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    asset_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    health_score = Column(Numeric(5, 2), nullable=False)
    anomaly_score = Column(Numeric(8, 6))
    metric_scores = Column(JSONB, default=dict)
    anomaly_flags = Column(ARRAY(String), default=list)
    alert_ids = Column(ARRAY(String), default=list)
    run_id = Column(UUID(as_uuid=True))
    ingested_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        PrimaryKeyConstraint("ts", "asset_id"),
        {
            "timescaledb_hypertable": {
                "time_column": "ts",
            }
        },
    )


class HealthAlert(Base):
    __tablename__ = "health_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    score_id = Column(UUID(as_uuid=True))
    title = Column(Text, nullable=False)
    description = Column(Text)
    severity = Column(String(12), nullable=False)
    status = Column(String(16), nullable=False, default="open")
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class MaintenanceWorkOrder(Base):
    __tablename__ = "maintenance_work_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("health_alerts.id", ondelete="SET NULL"))
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    priority = Column(String(12), nullable=False, default="medium")
    status = Column(String(16), nullable=False, default="scheduled")
    scheduled_start = Column(DateTime(timezone=True), nullable=False)
    scheduled_end = Column(DateTime(timezone=True), nullable=False)
    actual_start = Column(DateTime(timezone=True))
    actual_end = Column(DateTime(timezone=True))
    estimated_cost = Column(Numeric(12, 2))
    actual_cost = Column(Numeric(12, 2))
    parts_used = Column(JSONB, default=list)
    resolution_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    alert = relationship("HealthAlert", lazy="selectin")

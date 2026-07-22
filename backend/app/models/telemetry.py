import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Numeric, SmallInteger, func, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class TelemetryGeneration(Base):
    __tablename__ = "telemetry_generation"

    ts = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    asset_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    generation_kw = Column(Numeric(12, 4), nullable=False)
    energy_kwh = Column(Numeric(14, 4))
    power_factor = Column(Numeric(5, 4))
    voltage_v = Column(Numeric(8, 2))
    current_a = Column(Numeric(8, 2))
    frequency_hz = Column(Numeric(6, 3))
    temperature_c = Column(Numeric(6, 2))
    is_estimated = Column(Boolean, nullable=False, default=False)
    quality_code = Column(SmallInteger, default=0)
    ingested_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        PrimaryKeyConstraint("ts", "asset_id"),
        {
            "timescaledb_hypertable": {
                "time_column": "ts",
            }
        },
    )


class TelemetryWeather(Base):
    __tablename__ = "telemetry_weather"

    ts = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    site_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    temperature_c = Column(Numeric(6, 2))
    humidity_pct = Column(Numeric(5, 2))
    pressure_hpa = Column(Numeric(7, 1))
    wind_speed_ms = Column(Numeric(6, 2))
    wind_direction_deg = Column(Numeric(5, 1))
    solar_irradiance_wpm2 = Column(Numeric(8, 2))
    cloud_cover_pct = Column(Numeric(5, 2))
    precipitation_mm = Column(Numeric(8, 2))
    is_forecast = Column(Boolean, nullable=False, default=False)
    source = Column(Text, default="openweather")
    ingested_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        PrimaryKeyConstraint("ts", "site_id"),
        {
            "timescaledb_hypertable": {
                "time_column": "ts",
            }
        },
    )


class GridPrice(Base):
    __tablename__ = "grid_prices"

    ts = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    site_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    price_per_kwh = Column(Numeric(10, 6), nullable=False)
    currency = Column(Text, nullable=False, default="USD")
    source = Column(String(20), primary_key=True, nullable=False, default="real_time")
    market_region = Column(Text)
    is_forecast = Column(Boolean, nullable=False, default=False)
    extra_metadata = Column("metadata", JSONB, default=dict)

    __table_args__ = (
        PrimaryKeyConstraint("ts", "site_id", "source"),
        {
            "timescaledb_hypertable": {
                "time_column": "ts",
            }
        },
    )

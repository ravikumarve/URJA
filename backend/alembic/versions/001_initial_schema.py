"""Initial database schema — 20 tables with TimescaleDB hypertable support.

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-07-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

HYPERTABLES = [
    "telemetry_generation",
    "telemetry_weather",
    "grid_prices",
    "curtailment_events",
    "carbon_credits",
    "health_metrics",
]


def upgrade() -> None:
    # ---------------------------------------------------------------
    # 1. organizations
    # ---------------------------------------------------------------
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(), nullable=False, server_default=text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("logo_url", sa.Text(), nullable=True),
        sa.Column("timezone", sa.Text(), nullable=False, server_default=text("'UTC'")),
        sa.Column("currency", sa.Text(), nullable=False),
        sa.Column("emission_factor", sa.Numeric(8, 4), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=text("true")),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_organizations_slug"),
    )

    # ---------------------------------------------------------------
    # 2. users
    # ---------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(), nullable=False, server_default=text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "email", name="uq_users_org_email"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_users_organization_id", "users", ["organization_id"])

    # ---------------------------------------------------------------
    # 3. api_keys
    # ---------------------------------------------------------------
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(), nullable=False, server_default=text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(), nullable=False),
        sa.Column("key_prefix", sa.Text(), nullable=False),
        sa.Column("key_hash", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("scope", sa.String(8), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash", name="uq_api_keys_key_hash"),
        sa.UniqueConstraint("organization_id", "name", name="uq_api_keys_name_org"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_api_keys_organization_id", "api_keys", ["organization_id"])

    # ---------------------------------------------------------------
    # 4. asset_sites
    # ---------------------------------------------------------------
    op.create_table(
        "asset_sites",
        sa.Column("id", postgresql.UUID(), nullable=False, server_default=text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("capacity_mw", sa.Numeric(10, 4), nullable=False),
        sa.Column("timezone", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "code", name="uq_asset_sites_org_code"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_asset_sites_organization_id", "asset_sites", ["organization_id"])

    # ---------------------------------------------------------------
    # 5. assets
    # ---------------------------------------------------------------
    op.create_table(
        "assets",
        sa.Column("id", postgresql.UUID(), nullable=False, server_default=text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(), nullable=False),
        sa.Column("site_id", postgresql.UUID(), nullable=False),
        sa.Column("parent_asset_id", postgresql.UUID(), nullable=True),
        sa.Column("asset_type", sa.String(20), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("serial_number", sa.Text(), nullable=True),
        sa.Column("manufacturer", sa.Text(), nullable=True),
        sa.Column("model", sa.Text(), nullable=True),
        sa.Column("capacity_kw", sa.Numeric(12, 4), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("commissioning_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("health_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("config", postgresql.JSONB(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "code", name="uq_assets_org_code"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["site_id"], ["asset_sites.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_asset_id"], ["assets.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_assets_organization_id", "assets", ["organization_id"])
    op.create_index("ix_assets_site_id", "assets", ["site_id"])
    op.create_index("ix_assets_parent_asset_id", "assets", ["parent_asset_id"])

    # ---------------------------------------------------------------
    # 6. asset_relationships
    # ---------------------------------------------------------------
    op.create_table(
        "asset_relationships",
        sa.Column("id", postgresql.UUID(), nullable=False, server_default=text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(), nullable=False),
        sa.Column("parent_asset_id", postgresql.UUID(), nullable=False),
        sa.Column("child_asset_id", postgresql.UUID(), nullable=False),
        sa.Column("relationship_type", sa.String(20), nullable=False),
        sa.Column("position_index", sa.SmallInteger(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "parent_asset_id", "child_asset_id", "relationship_type", "ended_at",
            name="uq_asset_relationships_pair",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["child_asset_id"], ["assets.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_asset_relationships_organization_id", "asset_relationships", ["organization_id"])
    op.create_index("ix_asset_relationships_parent_asset_id", "asset_relationships", ["parent_asset_id"])
    op.create_index("ix_asset_relationships_child_asset_id", "asset_relationships", ["child_asset_id"])

    # ---------------------------------------------------------------
    # 7. telemetry_generation  (hypertable)
    # ---------------------------------------------------------------
    op.create_table(
        "telemetry_generation",
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(), nullable=False),
        sa.Column("organization_id", postgresql.UUID(), nullable=False),
        sa.Column("generation_kw", sa.Numeric(12, 4), nullable=False),
        sa.Column("energy_kwh", sa.Numeric(14, 4), nullable=True),
        sa.Column("power_factor", sa.Numeric(5, 4), nullable=True),
        sa.Column("voltage_v", sa.Numeric(8, 2), nullable=True),
        sa.Column("current_a", sa.Numeric(8, 2), nullable=True),
        sa.Column("frequency_hz", sa.Numeric(6, 3), nullable=True),
        sa.Column("temperature_c", sa.Numeric(6, 2), nullable=True),
        sa.Column("is_estimated", sa.Boolean(), nullable=False),
        sa.Column("quality_code", sa.SmallInteger(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.PrimaryKeyConstraint("ts", "asset_id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_telemetry_generation_organization_id", "telemetry_generation", ["organization_id"])
    op.create_index("ix_telemetry_generation_asset_id", "telemetry_generation", ["asset_id"])

    # ---------------------------------------------------------------
    # 8. telemetry_weather  (hypertable)
    # ---------------------------------------------------------------
    op.create_table(
        "telemetry_weather",
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("site_id", postgresql.UUID(), nullable=False),
        sa.Column("organization_id", postgresql.UUID(), nullable=False),
        sa.Column("temperature_c", sa.Numeric(6, 2), nullable=True),
        sa.Column("humidity_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("pressure_hpa", sa.Numeric(7, 1), nullable=True),
        sa.Column("wind_speed_ms", sa.Numeric(6, 2), nullable=True),
        sa.Column("wind_direction_deg", sa.Numeric(5, 1), nullable=True),
        sa.Column("solar_irradiance_wpm2", sa.Numeric(8, 2), nullable=True),
        sa.Column("cloud_cover_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("precipitation_mm", sa.Numeric(8, 2), nullable=True),
        sa.Column("is_forecast", sa.Boolean(), nullable=False),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.PrimaryKeyConstraint("ts", "site_id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_telemetry_weather_organization_id", "telemetry_weather", ["organization_id"])
    op.create_index("ix_telemetry_weather_site_id", "telemetry_weather", ["site_id"])

    # ---------------------------------------------------------------
    # 9. grid_prices  (hypertable)
    # ---------------------------------------------------------------
    op.create_table(
        "grid_prices",
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("site_id", postgresql.UUID(), nullable=False),
        sa.Column("organization_id", postgresql.UUID(), nullable=False),
        sa.Column("price_per_kwh", sa.Numeric(10, 6), nullable=False),
        sa.Column("currency", sa.Text(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("market_region", sa.Text(), nullable=True),
        sa.Column("is_forecast", sa.Boolean(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("ts", "site_id", "source"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_grid_prices_organization_id", "grid_prices", ["organization_id"])
    op.create_index("ix_grid_prices_site_id", "grid_prices", ["site_id"])

    # ---------------------------------------------------------------
    # 10. curtailment_events  (hypertable)
    # ---------------------------------------------------------------
    op.create_table(
        "curtailment_events",
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(), nullable=False, server_default=text("gen_random_uuid()")),
        sa.Column("asset_id", postgresql.UUID(), nullable=False),
        sa.Column("organization_id", postgresql.UUID(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("expected_kwh", sa.Numeric(14, 4), nullable=False),
        sa.Column("actual_kwh", sa.Numeric(14, 4), nullable=False),
        sa.Column("curtailed_kwh", sa.Numeric(14, 4), nullable=False),
        sa.Column("price_per_kwh", sa.Numeric(8, 4), nullable=False),
        sa.Column("revenue_lost", sa.Numeric(14, 4), nullable=False),
        sa.Column("grid_price_source", sa.Text(), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("ts", "event_id"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_curtailment_events_asset_id", "curtailment_events", ["asset_id"])
    op.create_index("ix_curtailment_events_organization_id", "curtailment_events", ["organization_id"])
    op.create_index("ix_curtailment_events_is_resolved", "curtailment_events", ["is_resolved"])

    # ---------------------------------------------------------------
    # 11. dispatch_rules
    # ---------------------------------------------------------------
    op.create_table(
        "dispatch_rules",
        sa.Column("id", postgresql.UUID(), nullable=False, server_default=text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("condition_type", sa.String(24), nullable=False),
        sa.Column("condition_config", postgresql.JSONB(), nullable=False),
        sa.Column("action", sa.String(22), nullable=False),
        sa.Column("action_config", postgresql.JSONB(), nullable=True),
        sa.Column("target_asset_type", sa.String(20), nullable=True),
        sa.Column("cooldown_minutes", sa.Integer(), nullable=False),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_dispatch_rules_organization_id", "dispatch_rules", ["organization_id"])

    # ---------------------------------------------------------------
    # 12. dispatch_decisions
    # ---------------------------------------------------------------
    op.create_table(
        "dispatch_decisions",
        sa.Column("id", postgresql.UUID(), nullable=False, server_default=text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(), nullable=False),
        sa.Column("rule_id", postgresql.UUID(), nullable=True),
        sa.Column("asset_id", postgresql.UUID(), nullable=False),
        sa.Column("curtailment_event_id", postgresql.UUID(), nullable=True),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("action_taken", sa.String(22), nullable=False),
        sa.Column("action_params", postgresql.JSONB(), nullable=True),
        sa.Column("triggered_value", sa.Numeric(14, 4), nullable=True),
        sa.Column("expected_outcome", sa.Numeric(14, 4), nullable=True),
        sa.Column("actual_outcome", sa.Numeric(14, 4), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_id"], ["dispatch_rules.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["curtailment_event_id"], ["curtailment_events.event_id"], ondelete="SET NULL",
        ),
    )
    op.create_index("ix_dispatch_decisions_organization_id", "dispatch_decisions", ["organization_id"])
    op.create_index("ix_dispatch_decisions_rule_id", "dispatch_decisions", ["rule_id"])
    op.create_index("ix_dispatch_decisions_asset_id", "dispatch_decisions", ["asset_id"])
    op.create_index(
        "ix_dispatch_decisions_curtailment_event_id", "dispatch_decisions", ["curtailment_event_id"],
    )
    op.create_index("ix_dispatch_decisions_status", "dispatch_decisions", ["status"])

    # ---------------------------------------------------------------
    # 13. carbon_credits  (hypertable)
    # ---------------------------------------------------------------
    op.create_table(
        "carbon_credits",
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("credit_id", postgresql.UUID(), nullable=False, server_default=text("gen_random_uuid()")),
        sa.Column("asset_id", postgresql.UUID(), nullable=False),
        sa.Column("organization_id", postgresql.UUID(), nullable=False),
        sa.Column("batch_id", postgresql.UUID(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column("methodology", sa.Text(), nullable=False),
        sa.Column("generation_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generation_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_kwh", sa.Numeric(14, 4), nullable=False),
        sa.Column("emission_factor", sa.Numeric(8, 4), nullable=False),
        sa.Column("registry_tx_id", sa.Text(), nullable=True),
        sa.Column("registry_url", sa.Text(), nullable=True),
        sa.Column("issued_by", postgresql.UUID(), nullable=True),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("ts", "credit_id"),
        sa.CheckConstraint("generation_end > generation_start", name="ck_carbon_generation_range"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["issued_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_carbon_credits_asset_id", "carbon_credits", ["asset_id"])
    op.create_index("ix_carbon_credits_organization_id", "carbon_credits", ["organization_id"])
    op.create_index("ix_carbon_credits_batch_id", "carbon_credits", ["batch_id"])
    op.create_index("ix_carbon_credits_status", "carbon_credits", ["status"])

    # ---------------------------------------------------------------
    # 14. health_metrics  (hypertable)
    # ---------------------------------------------------------------
    op.create_table(
        "health_metrics",
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(), nullable=False),
        sa.Column("organization_id", postgresql.UUID(), nullable=False),
        sa.Column("health_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("anomaly_score", sa.Numeric(8, 6), nullable=True),
        sa.Column("metric_scores", postgresql.JSONB(), nullable=True),
        sa.Column("anomaly_flags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("alert_ids", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("run_id", postgresql.UUID(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.PrimaryKeyConstraint("ts", "asset_id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_health_metrics_organization_id", "health_metrics", ["organization_id"])
    op.create_index("ix_health_metrics_asset_id", "health_metrics", ["asset_id"])

    # ---------------------------------------------------------------
    # 15. health_alerts
    # ---------------------------------------------------------------
    op.create_table(
        "health_alerts",
        sa.Column("id", postgresql.UUID(), nullable=False, server_default=text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(), nullable=False),
        sa.Column("asset_id", postgresql.UUID(), nullable=False),
        sa.Column("score_id", postgresql.UUID(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(12), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("acknowledged_by", postgresql.UUID(), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["acknowledged_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_health_alerts_organization_id", "health_alerts", ["organization_id"])
    op.create_index("ix_health_alerts_asset_id", "health_alerts", ["asset_id"])
    op.create_index("ix_health_alerts_severity", "health_alerts", ["severity"])
    op.create_index("ix_health_alerts_status", "health_alerts", ["status"])

    # ---------------------------------------------------------------
    # 16. maintenance_work_orders
    # ---------------------------------------------------------------
    op.create_table(
        "maintenance_work_orders",
        sa.Column("id", postgresql.UUID(), nullable=False, server_default=text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(), nullable=False),
        sa.Column("asset_id", postgresql.UUID(), nullable=False),
        sa.Column("alert_id", postgresql.UUID(), nullable=True),
        sa.Column("assigned_to", postgresql.UUID(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(12), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estimated_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("actual_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("parts_used", postgresql.JSONB(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["alert_id"], ["health_alerts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_maintenance_work_orders_organization_id", "maintenance_work_orders", ["organization_id"],
    )
    op.create_index("ix_maintenance_work_orders_asset_id", "maintenance_work_orders", ["asset_id"])
    op.create_index(
        "ix_maintenance_work_orders_assigned_to", "maintenance_work_orders", ["assigned_to"],
    )
    op.create_index("ix_maintenance_work_orders_status", "maintenance_work_orders", ["status"])

    # ---------------------------------------------------------------
    # 17. audit_log
    # ---------------------------------------------------------------
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("organization_id", postgresql.UUID(), nullable=False),
        sa.Column("actor_type", sa.String(12), nullable=False),
        sa.Column("actor_id", sa.Text(), nullable=False),
        sa.Column("action", sa.String(36), nullable=False),
        sa.Column("target_type", sa.Text(), nullable=True),
        sa.Column("target_id", sa.Text(), nullable=True),
        sa.Column("changes", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_audit_log_organization_id", "audit_log", ["organization_id"])
    op.create_index("ix_audit_log_action", "audit_log", ["action"])
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])

    # ---------------------------------------------------------------
    # 18. sessions
    # ---------------------------------------------------------------
    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(), nullable=False, server_default=text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(), nullable=False),
        sa.Column("organization_id", postgresql.UUID(), nullable=False),
        sa.Column("refresh_token_hash", sa.Text(), nullable=False),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("is_revoked", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("refresh_token_hash", name="uq_sessions_refresh_token_hash"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_organization_id", "sessions", ["organization_id"])
    op.create_index("ix_sessions_expires_at", "sessions", ["expires_at"])

    # ---------------------------------------------------------------
    # 19. email_notifications
    # ---------------------------------------------------------------
    op.create_table(
        "email_notifications",
        sa.Column("id", postgresql.UUID(), nullable=False, server_default=text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(), nullable=False),
        sa.Column("user_id", postgresql.UUID(), nullable=True),
        sa.Column("to_email", sa.Text(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_email_notifications_organization_id", "email_notifications", ["organization_id"],
    )
    op.create_index("ix_email_notifications_user_id", "email_notifications", ["user_id"])
    op.create_index("ix_email_notifications_status", "email_notifications", ["status"])

    # ---------------------------------------------------------------
    # 20. settings
    # ---------------------------------------------------------------
    op.create_table(
        "settings",
        sa.Column("id", postgresql.UUID(), nullable=False, server_default=text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(), nullable=False),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("value_type", sa.String(10), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_encrypted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "key", name="uq_settings_org_key"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_settings_organization_id", "settings", ["organization_id"])

    # ---------------------------------------------------------------
    # TimescaleDB hypertables
    # ---------------------------------------------------------------
    for table_name in HYPERTABLES:
        op.execute(
            f"SELECT create_hypertable('{table_name}', 'ts', if_not_exists => TRUE)"
        )


def downgrade() -> None:
    tables = [
        "settings",
        "email_notifications",
        "sessions",
        "audit_log",
        "maintenance_work_orders",
        "health_alerts",
        "health_metrics",
        "carbon_credits",
        "dispatch_decisions",
        "dispatch_rules",
        "curtailment_events",
        "grid_prices",
        "telemetry_weather",
        "telemetry_generation",
        "asset_relationships",
        "assets",
        "asset_sites",
        "api_keys",
        "users",
        "organizations",
    ]
    for table in tables:
        op.drop_table(table, if_exists=True)

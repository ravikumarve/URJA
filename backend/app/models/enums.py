import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    operator = "operator"
    viewer = "viewer"


class ApiKeyScope(str, enum.Enum):
    read = "read"
    write = "write"
    admin = "admin"


class SiteStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    decommissioned = "decommissioned"
    construction = "construction"


class AssetType(str, enum.Enum):
    solar_panel = "solar_panel"
    inverter = "inverter"
    wind_turbine = "wind_turbine"
    battery_storage = "battery_storage"
    meter = "meter"
    other = "other"


class AssetStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    maintenance = "maintenance"
    retired = "retired"


class RelationshipType(str, enum.Enum):
    contains = "contains"
    feeds_into = "feeds_into"
    monitors = "monitors"
    connected_to = "connected_to"


class DispatchAction(str, enum.Enum):
    charge_battery = "charge_battery"
    discharge_battery = "discharge_battery"
    route_to_compute = "route_to_compute"
    curtail_generation = "curtail_generation"
    notify_operator = "notify_operator"
    no_action = "no_action"


class DispatchConditionType(str, enum.Enum):
    price_above = "price_above"
    price_below = "price_below"
    curtailment_detected = "curtailment_detected"
    soc_above = "soc_above"
    soc_below = "soc_below"
    time_of_day = "time_of_day"
    generation_above = "generation_above"
    generation_below = "generation_below"


class DispatchStatus(str, enum.Enum):
    pending = "pending"
    executed = "executed"
    failed = "failed"
    skipped = "skipped"


class CreditStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    retired = "retired"
    cancelled = "cancelled"


class PriceSource(str, enum.Enum):
    day_ahead = "day_ahead"
    real_time = "real_time"
    historical = "historical"
    feed_in_tariff = "feed_in_tariff"
    ppa = "ppa"
    custom = "custom"


class AlertSeverity(str, enum.Enum):
    warning = "warning"
    critical = "critical"


class AlertStatus(str, enum.Enum):
    open = "open"
    acknowledged = "acknowledged"
    resolved = "resolved"


class MaintenancePriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class MaintenanceStatus(str, enum.Enum):
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    deferred = "deferred"


class AuditAction(str, enum.Enum):
    user_login = "user.login"
    user_logout = "user.logout"
    user_created = "user.created"
    user_role_changed = "user.role_changed"
    api_key_created = "api_key.created"
    api_key_revoked = "api_key.revoked"
    asset_created = "asset.created"
    asset_updated = "asset.updated"
    asset_decommissioned = "asset.decommissioned"
    dispatch_rule_created = "dispatch.rule_created"
    dispatch_rule_updated = "dispatch.rule_updated"
    dispatch_executed = "dispatch.executed"
    carbon_credit_minted = "carbon.credit_minted"
    carbon_credit_retired = "carbon.credit_retired"
    carbon_credit_cancelled = "carbon.credit_cancelled"
    health_alert_created = "health.alert_created"
    health_alert_acknowledged = "health.alert_acknowledged"
    maintenance_work_order_created = "maintenance.work_order_created"
    maintenance_work_order_completed = "maintenance.work_order_completed"
    settings_updated = "settings.updated"
    settings_branding_changed = "settings.branding_changed"
    telemetry_ingested = "telemetry.ingested"
    telemetry_batch_imported = "telemetry.batch_imported"
    maintenance_work_order_scheduled = "maintenance.work_order_scheduled"
    dispatch_rule_deleted = "dispatch.rule_deleted"


class EmailStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"
    bounced = "bounced"


class SettingType(str, enum.Enum):
    string = "string"
    number = "number"
    boolean = "boolean"
    json = "json"


class QualityCode(int, enum.Enum):
    good = 0
    suspect = 1
    estimated = 2
    bad = 3

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "URJA"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://urja:urja@localhost:5432/urja"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Auth
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_MINUTES: int = 10080

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Rate Limiting
    RATE_LIMIT_AUTH: int = 100
    RATE_LIMIT_UNAUTH: int = 10

    # TimescaleDB
    TELEMETRY_RETENTION_DAYS: int = 730
    TELEMETRY_CHUNK_INTERVAL_DAYS: int = 7
    TELEMETRY_COMPRESS_AFTER_DAYS: int = 30

    # Carbon
    CARBON_CREDIT_PER_MWH: float = 0.73
    MRV_METHODOLOGY_VERSION: str = "URJA-VCS-1.0"

    # Health
    HEALTH_ANOMALY_THRESHOLD: float = 0.15
    HEALTH_SCAN_INTERVAL_MINUTES: int = 60

    # Seed Data
    SEED_ORG_NAME: str = "GreenEnergy Corp"
    SEED_SITE_NAME: str = "Rajasthan Solar Farm"
    SEED_SITE_CAPACITY_MW: float = 50.0
    SEED_ADMIN_EMAIL: str = "admin@example.com"
    SEED_ADMIN_PASSWORD: str = "admin123"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()

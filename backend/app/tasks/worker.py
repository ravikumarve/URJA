import logging
from urllib.parse import urlparse

from arq.connections import RedisSettings
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_parsed = urlparse(settings.REDIS_URL)


async def startup(ctx):
    from app.database import async_session
    ctx["session_factory"] = async_session
    logger.info("ARQ worker started, DB session pool initialized")


async def shutdown(ctx):
    logger.info("ARQ worker shutdown")


class WorkerSettings:
    functions = []
    redis_settings = RedisSettings(
        host=_parsed.hostname or "localhost",
        port=_parsed.port or 6379,
        password=_parsed.password or None,
        database=int((_parsed.path or "/0").lstrip("/") or 0),
    )
    keep_result = 3600
    keep_result_failed = 86400
    max_retries = 3
    retry_delay = 5
    on_startup = startup
    on_shutdown = shutdown
    health_check_interval = 30


def get_worker_settings():
    from app.tasks.telemetry_ingest import process_telemetry_batch
    from app.tasks.carbon_mint import mint_carbon_credits
    from app.tasks.health_scan import health_scan
    from app.tasks.refresh_weather import refresh_weather_data
    from app.tasks.refresh_pricing import refresh_grid_pricing
    from app.tasks.daily_rollup import daily_rollup

    WorkerSettings.functions = [
        process_telemetry_batch,
        mint_carbon_credits,
        health_scan,
        refresh_weather_data,
        refresh_grid_pricing,
        daily_rollup,
    ]
    return WorkerSettings

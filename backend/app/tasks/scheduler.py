from arq import cron

from app.tasks.health_scan import health_scan
from app.tasks.refresh_weather import refresh_weather_data
from app.tasks.refresh_pricing import refresh_grid_pricing
from app.tasks.daily_rollup import daily_rollup

CRON_JOBS = [
    cron(health_scan, name="Health scan every 15 min", minute={0, 15, 30, 45}),
    cron(refresh_weather_data, name="Refresh weather every 6h", hour={0, 6, 12, 18}, minute=0),
    cron(refresh_grid_pricing, name="Refresh pricing every hour", hour={*range(24)}, minute=5),
    cron(daily_rollup, name="Daily rollup at 00:30", hour=0, minute=30),
]

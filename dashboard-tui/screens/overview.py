"""Overview screen — main tactical dashboard with KPIs, asset table, and worker log."""

from __future__ import annotations

from rich.text import Text as RichText

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, RichLog, Static

from widgets.kpi_card import KpiCard
from api import UrajaAPIClient


def _health_color(health: int) -> str:
    if health >= 80:
        return "#4ade80"
    if health >= 50:
        return "#ffb703"
    return "#ef4444"


class OverviewScreen(Screen):
    BINDINGS = []

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Static("URJA_CLI // TACTICAL_OPS", id="header-title"),
            Static(RichText("[DUST_STORM_ACTIVE]"), id="header-alert", classes="alert"),
            Static("SITE: ALPHA-01", id="header-status", classes="dim"),
            id="screen-header",
        )
        # KPI cards: title=floating panel badge, label=caption under value
        yield Horizontal(
            KpiCard(title="YIELD_MONITOR", label="LIVE GENERATION", id="kpi-mw", classes="kpi-card"),
            KpiCard(title="WEATHER_SYSTEM", label="WIND SPEED", id="kpi-wind", classes="kpi-card"),
            KpiCard(title="SOILING_RATIO", label="ALBEDO OCCLUSION", id="kpi-soil", classes="kpi-card"),
            KpiCard(title="REVENUE_LOST", label="TODAY", id="kpi-rev", classes="kpi-card"),
            id="kpi-row",
        )
        yield DataTable(id="asset-table")
        yield RichLog(id="worker-log", max_lines=12, highlight=True)
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#asset-table", DataTable).border_title = "ASSET_DIAGNOSTICS (3-SIGMA)"
        self.query_one("#worker-log", RichLog).border_title = "ARQ_WORKER_TAIL"
        self.set_interval(5, self.refresh_data)
        self.run_worker(self.refresh_data())

    async def refresh_data(self) -> None:
        api: UrajaAPIClient = self.app.api_client
        telemetry = await api.get_latest_telemetry()
        assets = await api.get_assets()
        alerts = await api.get_alerts()

        self._update_kpis(telemetry)
        self._update_asset_table(assets)
        self._update_worker_log(telemetry, alerts)

    def _update_kpis(self, telemetry: dict) -> None:
        self.query_one("#kpi-mw", KpiCard).value = f"{telemetry['current_mw']} MW"
        wind_card = self.query_one("#kpi-wind", KpiCard)
        wind_card.value = f"{telemetry['wind_speed']} KM/H"
        if telemetry.get("wind_speed", 0) > 40:
            wind_card.add_class("alert")
            wind_card.label = "WIND SHEAR - CRITICAL"
        else:
            wind_card.remove_class("alert")
            wind_card.label = "WIND SPEED"
        soil_card = self.query_one("#kpi-soil", KpiCard)
        soil_card.value = f"{telemetry['soiling_ratio']}%"
        if telemetry.get("soiling_ratio", 0) >= 75:
            soil_card.add_class("alert")
        else:
            soil_card.remove_class("alert")

        rev = telemetry.get("revenue_lost", 263480)
        self.query_one("#kpi-rev", KpiCard).value = f"₹{rev:,}"

        header_alert = self.query_one("#header-alert", Static)
        if telemetry.get("wind_speed", 0) > 40:
            header_alert.update(RichText("[DUST_STORM_ACTIVE]"))
            header_alert.classes = "alert blink"
        else:
            header_alert.update(RichText("[NOMINAL]"))
            header_alert.classes = "ok"

    def _update_asset_table(self, assets: list) -> None:
        table = self.query_one("#asset-table", DataTable)
        if not table.columns:
            table.add_columns("ASSET ID", "TYPE", "HEALTH", "TEMP", "STATUS")
        table.clear()
        for a in assets:
            health = a["health"]
            health_str = f"{health}%"
            temp_str = f"{a['temp']}C" if a["temp"] is not None else "--"
            status = a["status"]
            is_alert = health < 80 or status != "NOMINAL"
            if is_alert:
                from rich.text import Text
                health_col = _health_color(health)
                table.add_row(
                    Text(a["id"], style="#ff5e00"),
                    Text(a["type"], style="#ff5e00"),
                    Text(health_str, style=health_col),
                    Text(temp_str, style="#ff5e00" if a["temp"] and a["temp"] > 60 else "#ffb703"),
                    Text(status, style="#ff5e00"),
                )
            else:
                table.add_row(a["id"], a["type"], health_str, temp_str, status)

    def _update_worker_log(self, telemetry: dict, alerts: list) -> None:
        log = self.query_one("#worker-log", RichLog)
        log.clear()
        from datetime import datetime
        now = datetime.utcnow().strftime("%H:%M:%S")
        log.write(RichText(f"[{now}] ingest  : DNI dropped {100 - telemetry.get('irradiance', 500) / 10:.0f}%"))
        for alert in alerts[:2]:
            sev = "ALERT" if alert["severity"] == "critical" else "WARN"
            log.write(RichText(f"[{now}] health  : {alert['asset']} {sev}"))
        log.write(RichText(f"[{now}] dispatch: Grid price ₹{random_price():.1f}/kWh"))
        log.write(RichText(f"[{now}] weather : Wind {telemetry['wind_speed']} km/h"))


def random_price() -> float:
    import random
    return round(random.uniform(2.0, 4.5), 1)

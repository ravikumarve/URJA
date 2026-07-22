"""Health screen — asset scores, trends, anomalies, and active alerts."""

from __future__ import annotations

from rich.text import Text as RichText

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, RichLog, Static

from api import UrajaAPIClient


def _health_color(score: int) -> str:
    if score >= 80:
        return "#4ade80"
    if score >= 50:
        return "#ffb703"
    return "#ef4444"


class HealthScreen(Screen):
    BINDINGS = []

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Static("ASSET HEALTH SCORES", id="header-title"),
            Static(RichText("0"), id="header-alert-count", classes="alert"),
            Static("ACTIVE ALERTS", id="header-alert-label", classes="dim"),
            id="screen-header",
        )
        yield DataTable(id="health-table")
        yield RichLog(id="alerts-panel", max_lines=8, highlight=True)
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#health-table", DataTable).border_title = "ASSET_HEALTH (3-SIGMA)"
        self.query_one("#alerts-panel", RichLog).border_title = "ACTIVE_ALERTS"
        self.set_interval(5, self.refresh_data)
        self.run_worker(self.refresh_data())

    async def refresh_data(self) -> None:
        api: UrajaAPIClient = self.app.api_client
        scores = await api.get_health_scores()
        alerts = await api.get_alerts()

        self.query_one("#header-alert-count", Static).update(RichText(str(len(alerts))))
        self._update_health_table(scores)
        self._update_alerts_panel(alerts)

    def _update_health_table(self, scores: list) -> None:
        table = self.query_one("#health-table", DataTable)
        if not table.columns:
            table.add_columns("ASSET", "SCORE", "TREND", "ANOMALIES")
        table.clear()
        from rich.text import Text
        for s in scores:
            score = s["score"]
            color = _health_color(score)
            has_anomaly = s["anomalies"] != "None"
            anomaly_style = "#ff5e00" if has_anomaly else "#8a6300"
            trend_style = "#4ade80" if s["trend"] == "→" else "#ff5e00"
            table.add_row(
                Text(s["asset"], style="#ffb703"),
                Text(f"{score}%", style=f"bold {color}"),
                Text(s["trend"], style=trend_style),
                Text(s["anomalies"], style=anomaly_style),
            )

    def _update_alerts_panel(self, alerts: list) -> None:
        log = self.query_one("#alerts-panel", RichLog)
        log.clear()
        for a in alerts:
            prefix = "🔴" if a["severity"] == "critical" else "🟡"
            style = "#ef4444" if a["severity"] == "critical" else "#ffb703"
            from rich.text import Text
            log.write(Text(f"{prefix} {a['asset']}: {a['message']}", style=style))

"""Curtailment screen — events, revenue loss, and dispatch decisions."""

from __future__ import annotations

from rich.text import Text as RichText

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, RichLog, Static

from api import UrajaAPIClient


class CurtailmentScreen(Screen):
    BINDINGS = []

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Static("CURTAILMENT EVENTS — LAST 24H", id="header-title"),
            Static(RichText("₹0"), id="header-total-lost", classes="alert"),
            Static("TOTAL LOST", id="header-total-lost-label", classes="dim"),
            id="screen-header",
        )
        yield DataTable(id="curtailment-table")
        yield RichLog(id="dispatch-log", max_lines=8, highlight=True)
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#curtailment-table", DataTable).border_title = "CURTAILMENT EVENTS"
        self.query_one("#dispatch-log", RichLog).border_title = "DISPATCH_DECISIONS"
        self.set_interval(5, self.refresh_data)
        self.run_worker(self.refresh_data())

    async def refresh_data(self) -> None:
        api: UrajaAPIClient = self.app.api_client
        events = await api.get_curtailment_events()
        decisions = await api.get_dispatch_decisions()

        total_lost = sum(e["revenue_lost"] for e in events)
        self.query_one("#header-total-lost", Static).update(RichText(f"₹{total_lost:,}"))

        self._update_events_table(events)
        self._update_dispatch_log(decisions)

    def _update_events_table(self, events: list) -> None:
        table = self.query_one("#curtailment-table", DataTable)
        if not table.columns:
            table.add_columns("TIME", "DURATION", "CURTAILED", "PRICE", "REVENUE LOST", "STATUS")
        table.clear()
        from rich.text import Text
        for e in events:
            if e["severity"] == "critical":
                style = "#ef4444"
                status = "ACTIVE"
            elif e["severity"] == "warning":
                style = "#ffb703"
                status = "RESOLVED"
            else:
                style = "#8a6300"
                status = "HISTORICAL"
            table.add_row(
                Text(e["time"], style=style),
                Text(f"{e['duration']} min", style=style),
                Text(f"{e['curtailed']} MWh", style=style),
                Text(f"₹{e['price']}", style=style),
                Text(f"₹{e['revenue_lost']:,}", style=style),
                Text(status, style=style),
            )

    def _update_dispatch_log(self, decisions: list) -> None:
        log = self.query_one("#dispatch-log", RichLog)
        log.clear()
        for d in decisions:
            log.write(RichText(f"{d['time']}  {d['action']}"))

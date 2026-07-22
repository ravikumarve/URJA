"""Carbon screen — credit ledger with batch history."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Static

from widgets.kpi_card import KpiCard
from api import UrajaAPIClient


class CarbonScreen(Screen):
    BINDINGS = []

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Static("CARBON CREDIT LEDGER", id="header-title"),
            id="screen-header",
        )
        yield Horizontal(
            KpiCard(title="CREDITS_ISSUED", label="ISSUED", id="kpi-issued", classes="kpi-card"),
            KpiCard(title="CREDITS_RETIRED", label="RETIRED", id="kpi-retired", classes="kpi-card"),
            KpiCard(title="CREDITS_AVAILABLE", label="AVAILABLE", id="kpi-available", classes="kpi-card"),
            id="kpi-row",
        )
        yield DataTable(id="carbon-table")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#carbon-table", DataTable).border_title = "CREDIT_BATCHES"
        self.set_interval(5, self.refresh_data)
        self.run_worker(self.refresh_data())

    async def refresh_data(self) -> None:
        api: UrajaAPIClient = self.app.api_client
        credits = await api.get_carbon_credits()

        issued = sum(c["credits"] for c in credits if c["status"] == "active")
        pending = sum(c["credits"] for c in credits if c["status"] == "pending")
        retired = 1200
        total_issued = issued + pending
        available = total_issued - retired

        self.query_one("#kpi-issued", KpiCard).value = f"{total_issued:,}"
        self.query_one("#kpi-retired", KpiCard).value = f"{retired:,}"
        self.query_one("#kpi-available", KpiCard).value = f"{available:,}"

        self._update_credits_table(credits)

    def _update_credits_table(self, credits: list) -> None:
        table = self.query_one("#carbon-table", DataTable)
        if not table.columns:
            table.add_columns("BATCH ID", "DATE", "CO\u2082e", "CREDITS", "STATUS")
        table.clear()
        from rich.text import Text
        for c in credits:
            status_style = "#4ade80" if c["status"] == "active" else "#ffb703"
            table.add_row(
                Text(c["batch_id"], style="#ffb703"),
                Text(c["date"], style="#ffb703"),
                Text(f"{c['co2e']:,.1f}", style="#ffb703"),
                Text(f"{c['credits']:,}", style="#ffb703"),
                Text(c["status"], style=status_style),
            )

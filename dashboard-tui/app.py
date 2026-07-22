#!/usr/bin/env python3
"""URJA Tactical Ops TUI — Terminal dashboard for renewable energy ops."""

from __future__ import annotations

from textual.app import App
from textual.binding import Binding

from api import UrajaAPIClient
from screens.overview import OverviewScreen
from screens.curtailment import CurtailmentScreen
from screens.carbon import CarbonScreen
from screens.health import HealthScreen


class UrjaTUI(App):
    CSS_PATH = "theme.tcss"
    SCREENS = {
        "overview": OverviewScreen,
        "curtailment": CurtailmentScreen,
        "carbon": CarbonScreen,
        "health": HealthScreen,
    }
    BINDINGS = [
        Binding("1", "switch_screen('overview')", "Overview"),
        Binding("2", "switch_screen('curtailment')", "Curtailment"),
        Binding("3", "switch_screen('carbon')", "Carbon"),
        Binding("4", "switch_screen('health')", "Health"),
        Binding("r", "refresh_data", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    api_client: UrajaAPIClient

    def compose(self):
        return []

    def on_mount(self) -> None:
        self.api_client = UrajaAPIClient()
        self.push_screen("overview")

    def action_refresh_data(self) -> None:
        current = self.screen
        if hasattr(current, "refresh_data"):
            self.run_worker(current.refresh_data())

    def action_switch_screen(self, screen_name: str) -> None:
        self.switch_screen(screen_name)


if __name__ == "__main__":
    app = UrjaTUI()
    app.run()

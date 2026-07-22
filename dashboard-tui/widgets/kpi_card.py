"""KPI Card widget for URJA TUI dashboard."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widgets import Label, Static
from textual.widget import Widget


class KpiCard(Widget):
    value = reactive("--", init=False)
    label = reactive("", init=False)
    title = reactive("", init=False)

    def __init__(self, title: str = "", label: str = "", value: str = "--", **kwargs):
        super().__init__(**kwargs)
        self._init_title = title
        self._init_label = label
        self._init_value = value

    def compose(self) -> ComposeResult:
        yield Static(self._init_value, classes="value")
        yield Static(self._init_label, classes="label")
        yield Label(self._init_title, classes="title")

    def on_mount(self) -> None:
        self.title = self._init_title
        self.label = self._init_label
        self.value = self._init_value

    def watch_value(self, value: str) -> None:
        if self.is_mounted:
            self.query_one(".value", Static).update(value)

    def watch_label(self, label: str) -> None:
        if self.is_mounted:
            self.query_one(".label", Static).update(label)

    def watch_title(self, title: str) -> None:
        if self.is_mounted:
            self.query_one(".title", Label).update(title)

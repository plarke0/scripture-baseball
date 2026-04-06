from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual.containers import Container
from textual.widgets import Button, Select, Static

if TYPE_CHECKING:
    from client.app import ScriptureBaseballApp


class SetupPanel(Container):
    def compose(self):
        yield Static("[bold green]Choose Mode and Category[/bold green]", id="setup-title")
        yield Static("Mode")
        yield Select(options=[], id="mode-select")
        yield Static("Category")
        yield Select(options=[], id="category-select")
        yield Button("Start Game", id="start-game-button")
        yield Button("View Leaderboards", id="view-leaderboards-button")
        yield Button("Logout", id="logout-button")
        yield Static("", id="setup-status")

    def load_options(self, modes: list[dict], categories: list[dict]) -> None:
        mode_select = self.query_one("#mode-select", Select)
        category_select = self.query_one("#category-select", Select)
        mode_select.set_options([(mode["name"], mode["id"]) for mode in modes])
        category_select.set_options([(category["name"], category["id"]) for category in categories])
        if modes:
            mode_select.value = modes[0]["id"]
        if categories:
            category_select.value = categories[0]["id"]

    def set_status(self, message: str) -> None:
        self.query_one("#setup-status", Static).update(message)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app = cast("ScriptureBaseballApp", self.app)
        if event.button.id == "start-game-button":
            mode_id = self.query_one("#mode-select", Select).value
            category_id = self.query_one("#category-select", Select).value
            if mode_id is None or category_id is None:
                self.set_status("Select a mode and category before starting.")
                return
            app.start_game_flow(str(mode_id), str(category_id))
        elif event.button.id == "view-leaderboards-button":
            app.open_leaderboards()
        elif event.button.id == "logout-button":
            app.handle_logout()

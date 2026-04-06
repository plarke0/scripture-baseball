from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual.containers import Container
from textual.widgets import Button, Select, Static
from client.ui_theme import rich_text

if TYPE_CHECKING:
    from client.app import ScriptureBaseballApp


class LeaderboardPanel(Container):
    def compose(self):
        yield Static(rich_text("Leaderboards", "section_title", bold=True), id="leaderboard-title")
        yield Static("Mode")
        yield Select(options=[], id="leaderboard-mode-select")
        yield Static("Category")
        yield Select(options=[], id="leaderboard-category-select")
        yield Button("Refresh Leaderboard", id="refresh-leaderboard-button")
        yield Button("Back to Menu", id="leaderboard-back-button")
        yield Static("", id="leaderboard-status")
        yield Static("", id="leaderboard-content")

    def load_filters(self, modes: list[dict], categories: list[dict]) -> None:
        mode_select = self.query_one("#leaderboard-mode-select", Select)
        category_select = self.query_one("#leaderboard-category-select", Select)

        mode_select.set_options([(mode["name"], mode["id"]) for mode in modes])
        category_select.set_options([(category["name"], category["id"]) for category in categories])
        if modes:
            mode_select.value = modes[0]["id"]
        if categories:
            category_select.value = categories[0]["id"]

    def get_selected_mode_id(self) -> str | None:
        mode_id = self.query_one("#leaderboard-mode-select", Select).value
        if mode_id is None:
            return None
        return str(mode_id)

    def get_selected_category_id(self) -> str | None:
        category_id = self.query_one("#leaderboard-category-select", Select).value
        if category_id is None:
            return None
        return str(category_id)

    def set_status(self, message: str) -> None:
        self.query_one("#leaderboard-status", Static).update(message)

    def set_rows(self, heading: str, rows: list[str]) -> None:
        content = heading
        if rows:
            content += "\n" + "\n".join(rows)
        self.query_one("#leaderboard-content", Static).update(content)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app = cast("ScriptureBaseballApp", self.app)
        if event.button.id == "refresh-leaderboard-button":
            mode_id = self.get_selected_mode_id()
            category_id = self.get_selected_category_id()
            if mode_id is None or category_id is None:
                self.set_status("Select a mode and category first.")
                return
            app.refresh_leaderboard(category_id, mode_id)
        elif event.button.id == "leaderboard-back-button":
            app.return_to_setup()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id not in {"leaderboard-category-select", "leaderboard-mode-select"}:
            return
        if event.value is Select.BLANK:
            return
        app = cast("ScriptureBaseballApp", self.app)
        mode_id = self.get_selected_mode_id()
        category_id = self.get_selected_category_id()
        if mode_id is None or category_id is None:
            return
        app.refresh_leaderboard(category_id, mode_id)

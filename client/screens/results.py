from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual.containers import Container
from textual.widgets import Button, Static

if TYPE_CHECKING:
    from client.app import ScriptureBaseballApp


class ResultsPanel(Container):
    def compose(self):
        yield Static("Game Complete", id="results-title")
        yield Static("", id="final-score")
        yield Static("", id="results-message")
        yield Button("Play Again", id="play-again-button")
        yield Button("Logout", id="results-logout-button")

    def set_results(self, final_score: float, message: str) -> None:
        self.query_one("#final-score", Static).update(f"Final Score: {final_score}")
        self.query_one("#results-message", Static).update(message)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app = cast("ScriptureBaseballApp", self.app)
        if event.button.id == "play-again-button":
            app.start_new_game()
        elif event.button.id == "results-logout-button":
            app.handle_logout()

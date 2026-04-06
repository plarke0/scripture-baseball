from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual.containers import Container
from textual.widgets import Button, Static

if TYPE_CHECKING:
    from client.app import ScriptureBaseballApp


class ConfirmExitPanel(Container):
    def compose(self):
        yield Static("[bold yellow]Leave Current Game?[/bold yellow]", id="confirm-exit-title")
        yield Static(
            "If you leave now, your current score will be submitted and you will return to the menu.",
            id="confirm-exit-message",
        )
        yield Button("Confirm Leave", id="confirm-leave-button")
        yield Button("Cancel", id="cancel-leave-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app = cast("ScriptureBaseballApp", self.app)
        if event.button.id == "confirm-leave-button":
            app.confirm_exit_game()
        elif event.button.id == "cancel-leave-button":
            app.cancel_exit_game()

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual.containers import Container
from textual.widgets import Button, Input, Static
from client.ui_theme import rich_text

if TYPE_CHECKING:
    from client.app import ScriptureBaseballApp


class LoginPanel(Container):
    def compose(self):
        yield Static(rich_text("Scripture Baseball", "heading", bold=True), id="login-title")
        yield Static("Username")
        yield Input(placeholder="Username", id="login-username")
        yield Static("Password")
        yield Input(placeholder="Password", password=True, id="login-password")
        yield Button("Login", id="login-submit-button")
        yield Button("Need an account? Register", id="to-register-button")
        yield Static("", id="login-status")

    def set_status(self, message: str) -> None:
        self.query_one("#login-status", Static).update(message)

    def clear_form(self) -> None:
        self.query_one("#login-username", Input).value = ""
        self.query_one("#login-password", Input).value = ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app = cast("ScriptureBaseballApp", self.app)
        if event.button.id == "login-submit-button":
            username = self.query_one("#login-username", Input).value.strip()
            password = self.query_one("#login-password", Input).value
            app.handle_login(username, password)
        elif event.button.id == "to-register-button":
            app.show_register()

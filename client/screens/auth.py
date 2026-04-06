from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual.containers import Container
from textual.widgets import Button, Input, Static

if TYPE_CHECKING:
    from client.app import ScriptureBaseballApp


class AuthPanel(Container):
    def compose(self):
        yield Static("Scripture Baseball", id="auth-title")
        yield Static("Username")
        yield Input(placeholder="Username", id="username")
        yield Static("Email")
        yield Input(placeholder="Email", id="email")
        yield Static("Password")
        yield Input(placeholder="Password", password=True, id="password")
        yield Button("Login", id="login-button")
        yield Button("Register", id="register-button")
        yield Static("", id="auth-status")

    def set_status(self, message: str) -> None:
        self.query_one("#auth-status", Static).update(message)

    def clear_form(self) -> None:
        self.query_one("#username", Input).value = ""
        self.query_one("#email", Input).value = ""
        self.query_one("#password", Input).value = ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app = cast("ScriptureBaseballApp", self.app)
        username = self.query_one("#username", Input).value.strip()
        email = self.query_one("#email", Input).value.strip()
        password = self.query_one("#password", Input).value

        if event.button.id == "login-button":
            app.handle_login(username, password)
        elif event.button.id == "register-button":
            app.handle_register(username, email, password)

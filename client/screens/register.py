from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual.containers import Container
from textual.widgets import Button, Input, Static
from client.ui_theme import rich_text

if TYPE_CHECKING:
    from client.app import ScriptureBaseballApp


class RegisterPanel(Container):
    def compose(self):
        yield Static(rich_text("Create Account", "heading", bold=True), id="register-title")
        yield Static("Username")
        yield Input(placeholder="Username", id="register-username")
        yield Static("Email")
        yield Input(placeholder="Email", id="register-email")
        yield Static("Password")
        yield Input(placeholder="Password", password=True, id="register-password")
        yield Button("Register", id="register-submit-button")
        yield Button("Have an account? Login", id="to-login-button")
        yield Static("", id="register-status")

    def set_status(self, message: str) -> None:
        self.query_one("#register-status", Static).update(message)

    def clear_form(self) -> None:
        self.query_one("#register-username", Input).value = ""
        self.query_one("#register-email", Input).value = ""
        self.query_one("#register-password", Input).value = ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app = cast("ScriptureBaseballApp", self.app)
        if event.button.id == "register-submit-button":
            username = self.query_one("#register-username", Input).value.strip()
            email = self.query_one("#register-email", Input).value.strip()
            password = self.query_one("#register-password", Input).value
            app.handle_register(username, email, password)
        elif event.button.id == "to-login-button":
            app.show_login()

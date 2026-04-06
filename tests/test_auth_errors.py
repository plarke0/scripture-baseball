import unittest
from typing import Any, cast

from client.app import ScriptureBaseballApp


class _PanelStub:
    def __init__(self) -> None:
        self.status_messages: list[str] = []
        self.cleared: bool = False

    def set_status(self, message: str) -> None:
        self.status_messages.append(message)

    def clear_form(self) -> None:
        self.cleared = True


class _LoginSuccessResponse:
    def __init__(self, token: str = "token-123") -> None:
        self.auth_token = token


class _RegisterSuccessResponse:
    def __init__(self, token: str = "token-456") -> None:
        self.auth_token = token


class _FacadeLoginValueError:
    def login_user(self, _username: str, _password: str):
        raise ValueError("Incorrect password")


class _FacadeRegisterValueError:
    def register_user(self, _username: str, _email: str, _password: str):
        raise ValueError("Username already exists")


class _FacadeLoginUnexpectedError:
    def login_user(self, _username: str, _password: str):
        raise RuntimeError("DB is down")


class _FacadeRegisterUnexpectedError:
    def register_user(self, _username: str, _email: str, _password: str):
        raise RuntimeError("DB is down")


class _FacadeLoginMalformedResponse:
    def login_user(self, _username: str, _password: str):
        return object()


class _FacadeRegisterMalformedResponse:
    def register_user(self, _username: str, _email: str, _password: str):
        return object()


class _FacadeLoginSuccess:
    def login_user(self, _username: str, _password: str):
        return _LoginSuccessResponse()


class _FacadeRegisterSuccess:
    def register_user(self, _username: str, _email: str, _password: str):
        return _RegisterSuccessResponse()


class TestAuthErrorHandling(unittest.TestCase):
    def _build_app_with_stubs(self) -> tuple[ScriptureBaseballApp, _PanelStub, _PanelStub]:
        app = ScriptureBaseballApp()
        login_panel = _PanelStub()
        register_panel = _PanelStub()
        cast(Any, app).login_panel = login_panel
        cast(Any, app).register_panel = register_panel
        cast(Any, app)._enter_setup = lambda: None
        return app, login_panel, register_panel

    def test_login_value_error_sets_panel_status(self) -> None:
        app, login_panel, _ = self._build_app_with_stubs()
        cast(Any, app).facade = _FacadeLoginValueError()

        app.handle_login("alice", "bad-pass")

        self.assertEqual(login_panel.status_messages[-1], "Incorrect password")
        self.assertIsNone(app.session.auth_token)

    def test_register_value_error_sets_panel_status(self) -> None:
        app, _, register_panel = self._build_app_with_stubs()
        cast(Any, app).facade = _FacadeRegisterValueError()

        app.handle_register("alice", "alice@example.com", "secret")

        self.assertEqual(register_panel.status_messages[-1], "Username already exists")
        self.assertIsNone(app.session.auth_token)

    def test_login_unexpected_error_shows_generic_message(self) -> None:
        app, login_panel, _ = self._build_app_with_stubs()
        cast(Any, app).facade = _FacadeLoginUnexpectedError()

        app.handle_login("alice", "secret")

        self.assertEqual(login_panel.status_messages[-1], "Login failed. Please try again.")
        self.assertIsNone(app.session.auth_token)

    def test_register_unexpected_error_shows_generic_message(self) -> None:
        app, _, register_panel = self._build_app_with_stubs()
        cast(Any, app).facade = _FacadeRegisterUnexpectedError()

        app.handle_register("alice", "alice@example.com", "secret")

        self.assertEqual(register_panel.status_messages[-1], "Registration failed. Please try again.")
        self.assertIsNone(app.session.auth_token)

    def test_login_malformed_response_shows_generic_message(self) -> None:
        app, login_panel, _ = self._build_app_with_stubs()
        cast(Any, app).facade = _FacadeLoginMalformedResponse()

        app.handle_login("alice", "secret")

        self.assertEqual(login_panel.status_messages[-1], "Login failed. Please try again.")
        self.assertIsNone(app.session.auth_token)

    def test_register_malformed_response_shows_generic_message(self) -> None:
        app, _, register_panel = self._build_app_with_stubs()
        cast(Any, app).facade = _FacadeRegisterMalformedResponse()

        app.handle_register("alice", "alice@example.com", "secret")

        self.assertEqual(register_panel.status_messages[-1], "Registration failed. Please try again.")
        self.assertIsNone(app.session.auth_token)

    def test_login_success_preserves_happy_path(self) -> None:
        app, login_panel, _ = self._build_app_with_stubs()
        cast(Any, app).facade = _FacadeLoginSuccess()

        app.handle_login("alice", "secret")

        self.assertEqual(app.session.auth_token, "token-123")
        self.assertEqual(app.session.username, "alice")
        self.assertTrue(login_panel.cleared)
        self.assertEqual(login_panel.status_messages[-1], "Login successful.")

    def test_register_success_preserves_happy_path(self) -> None:
        app, _, register_panel = self._build_app_with_stubs()
        cast(Any, app).facade = _FacadeRegisterSuccess()

        app.handle_register("alice", "alice@example.com", "secret")

        self.assertEqual(app.session.auth_token, "token-456")
        self.assertEqual(app.session.username, "alice")
        self.assertTrue(register_panel.cleared)
        self.assertEqual(register_panel.status_messages[-1], "Registration successful.")


if __name__ == "__main__":
    unittest.main()

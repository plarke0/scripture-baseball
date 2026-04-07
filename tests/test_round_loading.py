import unittest
from typing import Any, cast
from unittest.mock import patch

from client.tk_app import TkScriptureBaseballApp
from shared.request_classes import VerseRequest
from shared.response_classes import VerseResponse


class _GameStub:
    def __init__(self) -> None:
        self._round_number = 0
        self._last_chapter_data: list[str] = []

    def start_round(self) -> VerseRequest:
        self._round_number += 1
        return VerseRequest("newtestament", "john", 3, 16)

    def get_round_number(self) -> int:
        return self._round_number

    def set_chapter_data(self, chapter_data: list[str]) -> None:
        self._last_chapter_data = chapter_data

    def get_round_state(self) -> dict[str, Any]:
        return {
            "round_number": self._round_number,
            "rounds_remaining": 4,
            "score": 0,
            "lives_remaining": 3,
            "hints_remaining": 3,
            "mode_id": "endless",
        }

    def is_game_over(self) -> bool:
        return False

    def get_hints_remaining(self) -> int:
        return 3


class _GamePanelStub:
    def __init__(self) -> None:
        self.hints: list[tuple[list[str], int | None]] = []
        self.prompts: list[str] = []
        self.feedback: list[str] = []
        self.controls: list[tuple[str, bool, bool]] = []
        self.round_states: list[tuple[int, int, int | None, int | None, str, bool]] = []

    def set_hint(self, lines: list[str], target: int | None) -> None:
        self.hints.append((lines, target))

    def set_prompt(self, prompt_text: str) -> None:
        self.prompts.append(prompt_text)

    def set_feedback(self, feedback_text: str) -> None:
        self.feedback.append(feedback_text)

    def clear_answer(self) -> None:
        return

    def set_controls(self, label: str, action_enabled: bool, hint_enabled: bool) -> None:
        self.controls.append((label, action_enabled, hint_enabled))

    def set_round_state(
        self,
        round_number: int,
        score: int,
        lives_remaining: int | None,
        hints_remaining: int | None,
        round_progress: str,
        is_endless: bool,
    ) -> None:
        self.round_states.append(
            (round_number, score, lives_remaining, hints_remaining, round_progress, is_endless)
        )


class _FacadeSuccessStub:
    def get_verse(self, _auth_token: str, _selected: VerseRequest) -> VerseResponse:
        return VerseResponse(["line 1", "line 2", "line 3"], "For God so loved the world")


class _ImmediateThread:
    def __init__(self, target, args=(), daemon=True) -> None:
        self._target = target
        self._args = args

    def start(self) -> None:
        self._target(*self._args)


class _NoopThread:
    def __init__(self, target, args=(), daemon=True) -> None:
        self._target = target
        self._args = args

    def start(self) -> None:
        return


class TestRoundLoading(unittest.TestCase):
    def _build_app_with_stubs(self) -> tuple[TkScriptureBaseballApp, _GamePanelStub, _GameStub]:
        app = TkScriptureBaseballApp(enable_ui=False)
        panel = _GamePanelStub()
        game = _GameStub()
        cast(Any, app).game_panel = panel
        cast(Any, app).game = game
        cast(Any, app).facade = _FacadeSuccessStub()
        cast(Any, app).show_panel = lambda _name: None
        cast(Any, app).root.after = lambda _delay, func: func()
        return app, panel, game

    def test_start_round_sets_loading_feedback_and_disables_controls(self) -> None:
        app, panel, _ = self._build_app_with_stubs()

        with patch("client.tk_app.threading.Thread", _NoopThread):
            app._start_round()

        self.assertTrue(app.session.is_round_loading)
        self.assertEqual(panel.prompts[-1], "Selecting verse...")
        self.assertEqual(panel.feedback[-1], "Selecting verse...")
        self.assertEqual(panel.controls[-1], ("Selecting Verse...", False, False))

    def test_round_fetch_success_clears_loading_and_sets_prompt(self) -> None:
        app, panel, game = self._build_app_with_stubs()

        with patch("client.tk_app.threading.Thread", _ImmediateThread):
            app._start_round()

        self.assertFalse(app.session.is_round_loading)
        self.assertEqual(panel.prompts[-1], "For God so loved the world")
        self.assertEqual(panel.feedback[-1], "")
        self.assertEqual(game._last_chapter_data, ["line 1", "line 2", "line 3"])

    def test_stale_round_response_is_ignored(self) -> None:
        app, panel, _ = self._build_app_with_stubs()
        app.session.is_round_loading = True
        app.session.round_request_id = 2
        panel.set_prompt("existing prompt")

        app._complete_round_fetch_success(
            1,
            VerseResponse(["ignored"], "ignored verse"),
        )

        self.assertTrue(app.session.is_round_loading)
        self.assertEqual(panel.prompts[-1], "existing prompt")

    def test_round_action_during_loading_shows_loading_feedback(self) -> None:
        app, panel, _ = self._build_app_with_stubs()
        app.session.is_round_loading = True

        app.handle_round_action("John 3:16")

        self.assertEqual(panel.feedback[-1], "Selecting verse...")


if __name__ == "__main__":
    unittest.main()

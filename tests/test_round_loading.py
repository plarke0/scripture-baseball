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
        self._game_over = False

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
        return self._game_over

    def get_hints_remaining(self) -> int:
        return 3

    def get_final_score(self) -> int:
        return 1200

    def get_available_modes(self) -> list[dict[str, str]]:
        return [{"id": "finite_5", "name": "Finite 5"}, {"id": "endless", "name": "Endless"}]

    def get_available_categories(self) -> list[dict[str, str]]:
        return [{"id": "new_testament", "name": "New Testament"}]


class _SetupPanelStub:
    def __init__(self) -> None:
        self.status_messages: list[str] = []

    def set_status(self, message: str) -> None:
        self.status_messages.append(message)


class _FacadeScoreStub:
    def __init__(self) -> None:
        self.calls = 0

    def update_highscore(self, _token: str, _leaderboard_key: str, _score: int) -> None:
        self.calls += 1


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

    def test_final_round_controls_show_play_again(self) -> None:
        app, panel, game = self._build_app_with_stubs()
        app.session.round_submitted = True
        game._game_over = True

        app._update_round_controls()

        self.assertEqual(panel.controls[-1], ("Play Again", True, False))

    def test_round_action_after_game_over_starts_new_game(self) -> None:
        app, _, game = self._build_app_with_stubs()
        app.session.round_submitted = True
        game._game_over = True
        started: list[bool] = []
        cast(Any, app).start_new_game = lambda: started.append(True)

        app.handle_round_action("ignored")

        self.assertEqual(started, [True])

    def test_return_to_menu_after_game_over_skips_confirmation(self) -> None:
        app, _, game = self._build_app_with_stubs()
        setup = _SetupPanelStub()
        app.setup_panel = cast(Any, setup)
        app.session.auth_token = "token"
        app._active_panel = "game"
        game._game_over = True

        panels: list[str] = []
        entered_setup: list[bool] = []
        cast(Any, app).show_panel = lambda name: panels.append(name)
        cast(Any, app)._enter_setup = lambda: entered_setup.append(True)
        cast(Any, app)._submit_current_score = lambda finalize_message: "saved"

        app.return_to_menu()

        self.assertEqual(entered_setup, [True])
        self.assertEqual(setup.status_messages[-1], "saved")
        self.assertNotIn("confirm-exit", panels)

    def test_return_to_menu_mid_game_shows_confirmation(self) -> None:
        app, _, game = self._build_app_with_stubs()
        app.session.auth_token = "token"
        app._active_panel = "game"
        game._game_over = False

        panels: list[str] = []
        cast(Any, app).show_panel = lambda name: panels.append(name)

        app.return_to_menu()

        self.assertIn("confirm-exit", panels)

    def test_submit_current_score_is_guarded_against_duplicate_saves(self) -> None:
        app, _, game = self._build_app_with_stubs()
        facade = _FacadeScoreStub()
        app.facade = cast(Any, facade)
        app.session.auth_token = "token"
        app.session.selected_category_id = "new_testament"
        app.session.selected_mode_id = "finite_5"
        app.session.current_round = 5
        game._round_number = 5

        first_message = app._submit_current_score(finalize_message=True)
        second_message = app._submit_current_score(finalize_message=True)

        self.assertIn("submitted successfully", first_message)
        self.assertIn("already submitted", second_message)
        self.assertEqual(facade.calls, 1)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import threading

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from client.facade_server import FacadeServer
from client.scoring_service import ScoringService
from client.session_state import ClientSessionState
from client.screens.confirm_exit import ConfirmExitPanel
from client.screens.game import GamePanel
from client.screens.leaderboard import LeaderboardPanel
from client.screens.login import LoginPanel
from client.screens.register import RegisterPanel
from client.screens.results import ResultsPanel
from client.screens.setup import SetupPanel
from client.ui_theme import rich_text
from shared.game import Game
from shared.request_classes import VerseRequest
from shared.response_classes import VerseResponse


class ScriptureBaseballApp(App):
    CSS = """
    Screen {
        align: center middle;
    }

    LoginPanel, RegisterPanel, SetupPanel, GamePanel, ConfirmExitPanel, ResultsPanel, LeaderboardPanel {
        width: 80%;
        max-width: 100;
        margin: 1 2;
        padding: 1 2;
        border: solid white;
        display: none;
    }

    #prompt-info {
        color: cyan;
    }

    #hint-output {
        color: magenta;
    }

    #feedback-output {
        color: yellow;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.facade: FacadeServer = FacadeServer()
        self.game: Game = Game()
        self.session: ClientSessionState = ClientSessionState()

        # Debounce state for leaderboard refresh
        self._leaderboard_debounce_timer: threading.Timer | None = None
        self._leaderboard_debounce_delay = 0.4  # seconds

        self.login_panel = LoginPanel(id="login-panel")
        self.register_panel = RegisterPanel(id="register-panel")
        self.setup_panel = SetupPanel(id="setup-panel")
        self.game_panel = GamePanel(id="game-panel")
        self.confirm_exit_panel = ConfirmExitPanel(id="confirm-exit-panel")
        self.results_panel = ResultsPanel(id="results-panel")
        self.leaderboard_panel = LeaderboardPanel(id="leaderboard-panel")

    def compose(self) -> ComposeResult:
        yield Header()
        yield self.login_panel
        yield self.register_panel
        yield self.setup_panel
        yield self.game_panel
        yield self.confirm_exit_panel
        yield self.results_panel
        yield self.leaderboard_panel
        yield Footer()

    def on_mount(self) -> None:
        self._show_only("login")
        self._refresh_setup_options()

    def handle_register(self, username: str, email: str, password: str) -> None:
        if not username or not email or not password:
            self.register_panel.set_status("Username, email, and password are required.")
            return

        try:
            response = self.facade.register_user(username, email, password)
        except ValueError as error:
            self.register_panel.set_status(str(error))
            return
        except Exception:
            self.register_panel.set_status("Registration failed. Please try again.")
            return

        auth_token = getattr(response, "auth_token", None)
        if not isinstance(auth_token, str) or len(auth_token.strip()) == 0:
            self.register_panel.set_status("Registration failed. Please try again.")
            return

        self.session.auth_token = response.auth_token
        self.session.username = username
        self.register_panel.clear_form()
        self.register_panel.set_status("Registration successful.")
        self._enter_setup()

    def handle_login(self, username: str, password: str) -> None:
        if not username or not password:
            self.login_panel.set_status("Username and password are required.")
            return

        try:
            response = self.facade.login_user(username, password)
        except ValueError as error:
            self.login_panel.set_status(str(error))
            return
        except Exception:
            self.login_panel.set_status("Login failed. Please try again.")
            return

        auth_token = getattr(response, "auth_token", None)
        if not isinstance(auth_token, str) or len(auth_token.strip()) == 0:
            self.login_panel.set_status("Login failed. Please try again.")
            return

        self.session.auth_token = response.auth_token
        self.session.username = username
        self.login_panel.clear_form()
        self.login_panel.set_status("Login successful.")
        self._enter_setup()

    def handle_logout(self) -> None:
        if self.session.auth_token:
            try:
                self.facade.logout_user(self.session.auth_token)
            except Exception:
                pass
        self.session = ClientSessionState()
        self.game = Game()
        self._refresh_setup_options()
        self._show_only("login")
        self.login_panel.set_status("Logged out.")

    def start_game_flow(self, mode_id: str, category_id: str) -> None:
        self.session.selected_mode_id = mode_id
        self.session.selected_category_id = category_id
        self.game.select_mode(mode_id)
        self.game.select_category(category_id)
        self.game.start_game()
        self.session.current_round = 0
        self.session.final_score = 0
        self.session.hint_lines = []
        self.session.hint_target_index = None
        self.session.round_submitted = False
        self.session.feedback = ""
        self._show_only("game")
        self._start_round()

    def start_new_game(self) -> None:
        if self.session.auth_token is None or self.session.selected_mode_id is None or self.session.selected_category_id is None:
            self._show_only("login")
            return
        self.game = Game()
        self.start_game_flow(self.session.selected_mode_id, self.session.selected_category_id)

    def show_login(self) -> None:
        self.register_panel.set_status("")
        self._show_only("login")

    def show_register(self) -> None:
        self.login_panel.set_status("")
        self._show_only("register")

    def open_leaderboards(self) -> None:
        self.leaderboard_panel.load_filters(
            self.game.get_available_modes(),
            self.game.get_available_categories(),
        )
        self.leaderboard_panel.set_status("Loading leaderboard...")
        self.leaderboard_panel.set_rows("", [])
        self._show_only("leaderboard")
        default_mode_id = self.leaderboard_panel.get_selected_mode_id()
        default_category_id = self.leaderboard_panel.get_selected_category_id()
        if default_mode_id is not None and default_category_id is not None:
            self.refresh_leaderboard(default_category_id, default_mode_id)

    def refresh_leaderboard(self, category_id: str, mode_id: str) -> None:
        if self.session.auth_token is None:
            self.leaderboard_panel.set_status("Login is required to view leaderboards.")
            return

        category_name = category_id
        mode_name = mode_id
        for category in self.game.get_available_categories():
            if category.get("id") == category_id:
                category_name = str(category.get("name", category_id))
                break
        for mode in self.game.get_available_modes():
            if mode.get("id") == mode_id:
                mode_name = str(mode.get("name", mode_id))
                break

        leaderboard_key = self._build_score_category_id(category_id, mode_id)
        try:
            top_scores = self.facade.get_top(self.session.auth_token, leaderboard_key, 10).top_scores
            my_score = self.facade.get_highscore(self.session.auth_token, leaderboard_key).highscore
        except Exception as error:
            self.leaderboard_panel.set_status(str(error))
            return

        rows: list[str] = []
        for index, score in enumerate(top_scores, start=1):
            rows.append(f"{index}. {score.username} - {score.highscore}")

        self.leaderboard_panel.set_rows(
            f"[bold]Top Scores ({category_name}: {mode_name})[/bold]\nYour Highscore: {my_score.highscore}",
            rows,
        )
        self.leaderboard_panel.set_status("")

    def debounce_leaderboard_refresh(self, category_id: str, mode_id: str) -> None:
        """Schedule a debounced leaderboard refresh to avoid rapid repeated fetches."""
        # Cancel any pending timer
        if self._leaderboard_debounce_timer:
            self._leaderboard_debounce_timer.cancel()
        
        # Increment request ID to track this refresh and ignore stale responses
        self.session.leaderboard_request_id += 1
        request_id = self.session.leaderboard_request_id
        
        # Show loading status
        self.leaderboard_panel.set_status("Updating scores...")
        
        # Schedule delayed refresh in background
        self._leaderboard_debounce_timer = threading.Timer(
            self._leaderboard_debounce_delay,
            lambda: self._fetch_leaderboard_in_background(request_id, category_id, mode_id)
        )
        self._leaderboard_debounce_timer.start()

    def _fetch_leaderboard_in_background(self, request_id: int, category_id: str, mode_id: str) -> None:
        """Fetch leaderboard data in a background thread."""
        try:
            if self.session.auth_token is None:
                self.call_from_thread(self._complete_leaderboard_fetch_error, request_id, "Login is required to view leaderboards.")
                return
            
            leaderboard_key = self._build_score_category_id(category_id, mode_id)
            top_scores = self.facade.get_top(self.session.auth_token, leaderboard_key, 10).top_scores
            my_score = self.facade.get_highscore(self.session.auth_token, leaderboard_key).highscore
            
            self.call_from_thread(self._complete_leaderboard_fetch, request_id, category_id, mode_id, top_scores, my_score)
        except Exception as error:
            self.call_from_thread(self._complete_leaderboard_fetch_error, request_id, str(error))

    def _complete_leaderboard_fetch(self, request_id: int, category_id: str, mode_id: str, top_scores: list, my_score) -> None:
        """Complete the leaderboard fetch and update UI if request is not stale."""
        # Ignore if a newer request has been scheduled
        if request_id != self.session.leaderboard_request_id:
            return
        
        # Get human-readable names for display
        category_name = category_id
        mode_name = mode_id
        for category in self.game.get_available_categories():
            if category.get("id") == category_id:
                category_name = str(category.get("name", category_id))
                break
        for mode in self.game.get_available_modes():
            if mode.get("id") == mode_id:
                mode_name = str(mode.get("name", mode_id))
                break
        
        # Build rows
        rows: list[str] = []
        for index, score in enumerate(top_scores, start=1):
            rows.append(f"{index}. {score.username} - {score.highscore}")
        
        # Update UI
        self.leaderboard_panel.set_rows(
            f"[bold]Top Scores ({category_name}: {mode_name})[/bold]\nYour Highscore: {my_score.highscore}",
            rows,
        )
        self.leaderboard_panel.set_status("")

    def _complete_leaderboard_fetch_error(self, request_id: int, error_message: str) -> None:
        """Complete the leaderboard fetch with an error if request is not stale."""
        # Ignore if a newer request has been scheduled
        if request_id != self.session.leaderboard_request_id:
            return
        
        self.leaderboard_panel.set_status(error_message)

    def next_round(self) -> None:
        if self.session.is_round_loading:
            self.game_panel.set_feedback(rich_text("Selecting verse...", "loading_state"))
            return
        if not self.session.round_submitted:
            self.game_panel.set_feedback(rich_text("Submit an answer before continuing.", "feedback_error"))
            return
        if self.game.is_game_over():
            self._finish_game()
            return
        self._start_round()

    def handle_round_action(self, answer_text: str) -> None:
        if self.session.is_round_loading:
            self.game_panel.set_feedback(rich_text("Selecting verse...", "loading_state"))
            return
        if self.session.round_submitted:
            self.next_round()
            return
        self.submit_answer(answer_text)

    def request_hint(self) -> None:
        if self.session.is_round_loading:
            self.game_panel.set_feedback(rich_text("Selecting verse...", "loading_state"))
            return
        if self.session.round_submitted:
            if self.game.is_game_over():
                self.game_panel.set_feedback(rich_text("Game is complete. Press End Game to view results.", "feedback_error"))
            else:
                self.game_panel.set_feedback(rich_text("Round complete. Start the next round or end the game.", "feedback_error"))
            return
        try:
            hint_payload = self.game.get_hint()
        except Exception as error:
            self.game_panel.set_feedback(str(error))
            return

        self.session.hint_lines = list(hint_payload["lines"])
        self.session.hint_target_index = int(hint_payload["target_index"])
        self.game_panel.set_hint(self.session.hint_lines, self.session.hint_target_index)
        self._refresh_game_panel()

    def submit_answer(self, answer_text: str) -> None:
        if not answer_text:
            self.game_panel.set_feedback(rich_text("Enter an answer before submitting.", "feedback_error"))
            return

        if self.session.round_submitted:
            if self.game.is_game_over():
                self.game_panel.set_feedback(rich_text("Game is complete. Press End Game to view results.", "feedback_error"))
            else:
                self.game_panel.set_feedback(rich_text("Round complete. Start the next round or end the game.", "feedback_error"))
            return

        try:
            result = self.game.submit_answer(answer_text)
        except Exception as error:
            self.game_panel.set_feedback(str(error))
            return

        points = self._score_answer(result["closeness"])
        self.game.add_score(points)

        self.session.final_score = self.game.get_final_score()
        self.session.feedback = self._format_submission_feedback(
            result["closeness"],
            points,
            result["life_lost"],
            result["lives_remaining"],
        )
        self.game_panel.set_feedback(self.session.feedback)
        self.game_panel.clear_answer()
        self.session.round_submitted = True
        self._refresh_game_panel()

    def return_to_setup(self) -> None:
        self._enter_setup()

    def return_to_menu(self) -> None:
        if self.session.auth_token is None:
            self._show_only("login")
            return
        if self.game_panel.display:
            self._show_only("confirm-exit")
            return
        self._enter_setup()

    def confirm_exit_game(self) -> None:
        message = self._submit_current_score(finalize_message=False)
        self._enter_setup()
        self.setup_panel.set_status(message)

    def cancel_exit_game(self) -> None:
        self._show_only("game")

    def _start_round(self) -> None:
        if self.session.is_round_loading:
            return

        selected = self.game.start_round()
        self.session.current_round = self.game.get_round_number()
        self.session.current_target = selected
        self.session.hint_lines = []
        self.session.hint_target_index = None
        self.session.round_submitted = False
        self.session.feedback = rich_text("Selecting verse...", "loading_state")
        self.session.is_round_loading = True
        self.session.round_request_id += 1
        request_id = self.session.round_request_id

        self._show_only("game")
        self.game_panel.set_hint([], None)
        self.game_panel.set_prompt(rich_text("Selecting verse...", "supporting_text", dim=True))
        self._refresh_game_panel()
        self.game_panel.clear_answer()
        self.game_panel.set_feedback(self.session.feedback)
        self._update_round_controls()

        fetch_thread = threading.Thread(
            target=self._fetch_round_verse,
            args=(request_id, selected),
            daemon=True,
        )
        fetch_thread.start()

    def _fetch_round_verse(self, request_id: int, selected: VerseRequest) -> None:
        try:
            verse_response = self.facade.get_verse(self.session.auth_token or "", selected)
        except Exception as error:
            self.call_from_thread(self._complete_round_fetch_error, request_id, str(error))
            return

        self.call_from_thread(self._complete_round_fetch_success, request_id, verse_response)

    def _complete_round_fetch_success(self, request_id: int, verse_response: VerseResponse) -> None:
        if request_id != self.session.round_request_id:
            return

        self.session.is_round_loading = False
        self.game.set_chapter_data(verse_response.chapter)
        self.session.feedback = ""
        self.game_panel.set_prompt(verse_response.verse)
        self.game_panel.set_feedback("")
        self._refresh_game_panel()

    def _complete_round_fetch_error(self, request_id: int, error_message: str) -> None:
        if request_id != self.session.round_request_id:
            return

        self.session.is_round_loading = False
        self.session.feedback = rich_text(f"Unable to load verse: {error_message}", "feedback_error")
        self.game_panel.set_prompt(rich_text("Verse unavailable", "supporting_text", dim=True))
        self.game_panel.set_feedback(self.session.feedback)
        self._refresh_game_panel()

    def _finish_game(self) -> None:
        message = self._submit_current_score(finalize_message=True)
        self.results_panel.set_results(self.session.final_score, message)

        self._show_only("results")

    def _enter_setup(self) -> None:
        self._refresh_setup_options()
        self.setup_panel.set_status("")
        self._show_only("setup")

    def _refresh_setup_options(self) -> None:
        self.setup_panel.load_options(self.game.get_available_modes(), self.game.get_available_categories())

    def _refresh_game_panel(self) -> None:
        state = self.game.get_round_state()
        round_progress = str(state["round_number"])
        if state["rounds_remaining"] is not None:
            total_rounds = state["round_number"] + state["rounds_remaining"]
            round_progress = f"{state['round_number']} / {total_rounds}"

        self.game_panel.set_round_state(
            state["round_number"],
            state["score"],
            state["lives_remaining"],
            state["hints_remaining"],
            round_progress,
            state["mode_id"] == "endless",
        )
        self._update_round_controls()

    def _update_round_controls(self) -> None:
        if self.session.is_round_loading:
            self.game_panel.set_controls(
                "Selecting Verse...",
                False,
                False,
            )
            return

        if self.session.round_submitted:
            if self.game.is_game_over():
                self.game_panel.set_controls(
                    "End Game",
                    True,
                    False,
                )
                return

            self.game_panel.set_controls(
                "Next Round",
                not self.game.is_game_over(),
                False,
            )
            return

        self.game_panel.set_controls(
            "Submit Answer",
            True,
            self.game.get_hints_remaining() != 0,
        )

    def _submit_current_score(self, finalize_message: bool) -> str:
        self.session.final_score = self.game.get_final_score()
        mode_name = self._get_mode_name(self.session.selected_mode_id)
        rounds_played = self.session.current_round
        if self.session.auth_token and self.session.selected_category_id and self.session.selected_mode_id:
            leaderboard_key = self._build_score_category_id(
                self.session.selected_category_id,
                self.session.selected_mode_id,
            )
            try:
                self.facade.update_highscore(
                    self.session.auth_token,
                    leaderboard_key,
                    self.session.final_score,
                )
            except Exception as error:
                if finalize_message:
                    return f"Game over, but score submission failed: {error}"
                return f"Returned to menu, but score submission failed: {error}"

            if finalize_message:
                return (
                    f"Completed {rounds_played} rounds in {mode_name}. "
                    "Score submitted successfully."
                )
            return (
                f"Returned to menu from {mode_name} after {rounds_played} rounds. "
                "Current score submitted successfully."
            )

        if finalize_message:
            return "Game over."
        return "Returned to menu."

    def _score_answer(self, closeness: dict) -> int:
        return ScoringService.score_answer(
            closeness,
            self.game.get_scoring_config(),
            self.game.get_selected_category_metrics(),
            self.session.selected_mode_id,
            self.game.get_hints_used_this_round(),
        )

    def _format_submission_feedback(
        self,
        closeness: dict,
        points: int,
        life_lost: bool,
        _lives_remaining: int | None,
    ) -> str:
        return ScoringService.format_submission_feedback(
            closeness=closeness,
            points=points,
            life_lost=life_lost,
            selected_mode_id=self.session.selected_mode_id,
            hints_used_this_round=self.game.get_hints_used_this_round(),
            scoring_config=self.game.get_scoring_config(),
            correct_answer=self.game.get_correct_answer(),
            style=lambda text, theme_key: rich_text(text, theme_key, dim=(theme_key == "supporting_text")),
        )

    def _format_distance_phrase(self, closeness: dict) -> str:
        return ScoringService.format_distance_phrase(closeness)

    def _get_mode_name(self, mode_id: str | None) -> str:
        if mode_id is None:
            return "this mode"
        for mode in self.game.get_available_modes():
            if mode.get("id") == mode_id:
                return str(mode.get("name", mode_id))
        return mode_id

    def _show_only(self, visible_panel: str) -> None:
        panels = {
            "login": self.login_panel,
            "register": self.register_panel,
            "setup": self.setup_panel,
            "game": self.game_panel,
            "confirm-exit": self.confirm_exit_panel,
            "results": self.results_panel,
            "leaderboard": self.leaderboard_panel,
        }
        for name, panel in panels.items():
            panel.display = name == visible_panel

    @staticmethod
    def _build_score_category_id(category_id: str, mode_id: str) -> str:
        return f"{category_id}-{mode_id}"


if __name__ == "__main__":
    ScriptureBaseballApp().run()

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from client.facade_server import FacadeServer
from client.session_state import ClientSessionState
from client.screens.game import GamePanel
from client.screens.leaderboard import LeaderboardPanel
from client.screens.login import LoginPanel
from client.screens.register import RegisterPanel
from client.screens.results import ResultsPanel
from client.screens.setup import SetupPanel
from shared.game import Game


class ScriptureBaseballApp(App):
    CSS = """
    Screen {
        align: center middle;
    }

    LoginPanel, RegisterPanel, SetupPanel, GamePanel, ResultsPanel, LeaderboardPanel {
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

        self.login_panel = LoginPanel(id="login-panel")
        self.register_panel = RegisterPanel(id="register-panel")
        self.setup_panel = SetupPanel(id="setup-panel")
        self.game_panel = GamePanel(id="game-panel")
        self.results_panel = ResultsPanel(id="results-panel")
        self.leaderboard_panel = LeaderboardPanel(id="leaderboard-panel")

    def compose(self) -> ComposeResult:
        yield Header()
        yield self.login_panel
        yield self.register_panel
        yield self.setup_panel
        yield self.game_panel
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

        response = self.facade.register_user(username, email, password)
        self.session.auth_token = response.auth_token
        self.session.username = username
        self.register_panel.clear_form()
        self.register_panel.set_status("Registration successful.")
        self._enter_setup()

    def handle_login(self, username: str, password: str) -> None:
        if not username or not password:
            self.login_panel.set_status("Username and password are required.")
            return

        response = self.facade.login_user(username, password)
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
        self.session.final_score = 0.0
        self.session.hint_lines = []
        self.session.feedback = ""
        self._show_only("game")
        self._start_round()

    def start_new_game(self) -> None:
        if self.session.auth_token is None:
            self._show_only("login")
            return
        self.game = Game()
        self._refresh_setup_options()
        self._enter_setup()

    def show_login(self) -> None:
        self.register_panel.set_status("")
        self._show_only("login")

    def show_register(self) -> None:
        self.login_panel.set_status("")
        self._show_only("register")

    def open_leaderboards(self) -> None:
        self.leaderboard_panel.load_categories(self.game.get_available_categories())
        self.leaderboard_panel.set_status("")
        self.leaderboard_panel.set_rows("Select a category and refresh.", [])
        self._show_only("leaderboard")

    def refresh_leaderboard(self, category_id: str) -> None:
        if self.session.auth_token is None:
            self.leaderboard_panel.set_status("Login is required to view leaderboards.")
            return
        try:
            top_scores = self.facade.get_top(self.session.auth_token, category_id, 10).top_scores
            my_score = self.facade.get_highscore(self.session.auth_token, category_id).highscore
        except Exception as error:
            self.leaderboard_panel.set_status(str(error))
            return

        rows: list[str] = []
        for index, score in enumerate(top_scores, start=1):
            rows.append(f"{index}. {score.username} - {score.highscore}")

        self.leaderboard_panel.set_rows(
            f"[bold]Top Scores ({category_id})[/bold]\nYour Highscore: {my_score.highscore}",
            rows,
        )
        self.leaderboard_panel.set_status("Leaderboard updated.")

    def next_round(self) -> None:
        if self.game.is_game_over():
            self._finish_game()
            return
        self._start_round()

    def request_hint(self) -> None:
        try:
            hint_lines = self.game.get_hint()
        except Exception as error:
            self.game_panel.set_feedback(str(error))
            return

        self.session.hint_lines = hint_lines
        self.game_panel.set_hint(hint_lines)
        self._refresh_game_panel()

    def submit_answer(self, answer_text: str) -> None:
        if not answer_text:
            self.game_panel.set_feedback("Enter an answer before submitting.")
            return

        try:
            result = self.game.submit_answer(answer_text)
        except Exception as error:
            self.game_panel.set_feedback(str(error))
            return

        points = self._score_answer(result["closeness"])
        if points > 0:
            self.game.add_score(points)

        self.session.final_score = self.game.get_final_score()
        self.session.feedback = self._format_submission_feedback(result["closeness"], points)
        self.game_panel.set_feedback(self.session.feedback)
        self.game_panel.clear_answer()
        self._refresh_game_panel()

        if self.game.is_game_over():
            self._finish_game()

    def return_to_setup(self) -> None:
        if self.session.auth_token is None:
            self._show_only("login")
            return
        self._enter_setup()

    def _start_round(self) -> None:
        selected = self.game.start_round()
        self.session.current_round = self.game.get_round_number()
        self.session.current_target = selected
        verse_response = self.facade.get_verse(self.session.auth_token or "", selected)
        self.game.set_chapter_data(verse_response.chapter)
        self.session.hint_lines = []
        self.session.feedback = ""
        self._show_only("game")
        self.game_panel.set_hint([])
        self.game_panel.set_prompt(verse_response.verse)
        self._refresh_game_panel()
        self.game_panel.clear_answer()
        self.game_panel.set_feedback("")
        self.game_panel.set_controls(True, True, False)

    def _finish_game(self) -> None:
        self.session.final_score = self.game.get_final_score()
        if self.session.auth_token and self.session.selected_category_id:
            try:
                self.facade.update_highscore(
                    self.session.auth_token,
                    self.session.selected_category_id,
                    self.session.final_score,
                )
            except Exception as error:
                self.results_panel.set_results(
                    self.session.final_score,
                    f"Game over, but score submission failed: {error}",
                )
            else:
                self.results_panel.set_results(
                    self.session.final_score,
                    "Score submitted successfully.",
                )
        else:
            self.results_panel.set_results(self.session.final_score, "Game over.")

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
            round_progress,
            state["rounds_remaining"],
        )
        self.game_panel.set_controls(True, self.game.get_hints_remaining() != 0, not self.game.is_game_over())

    def _score_answer(self, closeness: dict) -> float:
        if not closeness.get("is_exact"):
            return 0.0
        if self.session.selected_mode_id == "endless":
            return 1.0
        return 0.5

    def _format_submission_feedback(self, closeness: dict, points: float) -> str:
        unit = closeness.get("unit")
        offset = closeness.get("offset")
        correct_answer = self.game.get_correct_answer()
        delta_prefix = "+" if points >= 0 else ""
        if closeness.get("is_exact"):
            return (
                f"[green]Exact![/green] Correct answer: [bold]{correct_answer}[/bold] "
                f"({delta_prefix}{points} points, total {self.game.get_final_score()})."
            )
        return (
            f"[yellow]Not exact.[/yellow] Correct answer: [bold]{correct_answer}[/bold]. "
            f"Closest unit: {unit} (offset {offset}). "
            f"Points change: {delta_prefix}{points}. Total: {self.game.get_final_score()}."
        )

    def _show_only(self, visible_panel: str) -> None:
        panels = {
            "login": self.login_panel,
            "register": self.register_panel,
            "setup": self.setup_panel,
            "game": self.game_panel,
            "results": self.results_panel,
            "leaderboard": self.leaderboard_panel,
        }
        for name, panel in panels.items():
            panel.display = name == visible_panel


if __name__ == "__main__":
    ScriptureBaseballApp().run()

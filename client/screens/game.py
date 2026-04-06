from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual.containers import Container
from textual.widgets import Button, Input, Static
from client.ui_theme import rich_text

if TYPE_CHECKING:
    from client.app import ScriptureBaseballApp


class GamePanel(Container):
    def compose(self):
        yield Static(rich_text("Game In Progress", "title", bold=True), id="game-title")
        yield Static("", id="round-info")
        yield Static("", id="score-info")
        yield Static("", id="lives-info")
        yield Static("", id="hints-remaining-info")
        yield Static(rich_text("Verse to Guess", "heading", bold=True), id="prompt-label")
        yield Static("", id="prompt-info")
        yield Static(rich_text("--------------------", "separator", dim=True), id="prompt-separator")
        yield Static(rich_text("Hint Verses", "hint_label", bold=True), id="hint-label")
        yield Static("", id="hint-output")
        yield Static("", id="feedback-output")
        yield Input(placeholder="Book Chapter:Verse", id="answer-input")
        yield Button("Submit Answer", id="round-action-button")
        yield Button("Get Hint", id="hint-button")
        yield Button("Back to Menu", id="back-to-menu-button")

    def set_round_state(
        self,
        round_number: int,
        score: int,
        lives_remaining: int | None,
        hints_remaining: int | None,
        round_progress: str,
        is_endless: bool,
    ) -> None:
        self.query_one("#round-info", Static).update(f"[bold]Round:[/bold] {round_progress}")
        points_label = rich_text("Points:", "score_label", bold=True)
        self.query_one("#score-info", Static).update(f"{points_label} {score}")
        lives_text = ""
        if is_endless:
            lives_label = rich_text("Lives:", "lives_label", bold=True)
            lives_text = f"{lives_label} {lives_remaining if lives_remaining is not None else '--'}"
        self.query_one("#lives-info", Static).update(lives_text)

        hints_text = ""
        if is_endless:
            hints_label = rich_text("Hints Remaining:", "hint_label", bold=True)
            hints_text = f"{hints_label} {hints_remaining if hints_remaining is not None else '--'}"
        self.query_one("#hints-remaining-info", Static).update(hints_text)

    def set_prompt(self, prompt_text: str) -> None:
        self.query_one("#prompt-info", Static).update(rich_text(prompt_text, "selected_verse", bold=True))

    def set_hint(self, hint_lines: list[str], target_index: int | None = None) -> None:
        hint_label = self.query_one("#hint-label", Static)
        hint_output = self.query_one("#hint-output", Static)

        if len(hint_lines) == 0:
            hint_label.display = False
            hint_output.display = False
            hint_output.update("")
            return

        hint_label.display = True
        hint_output.display = True

        colored_lines: list[str] = []
        for index, line in enumerate(hint_lines):
            if target_index is not None and index == target_index:
                colored_lines.append(rich_text(line, "selected_verse", bold=True))
            else:
                colored_lines.append(rich_text(line, "hint"))

        hint_output.update("\n".join(colored_lines))

    def set_feedback(self, feedback_text: str) -> None:
        self.query_one("#feedback-output", Static).update(feedback_text)

    def clear_answer(self) -> None:
        self.query_one("#answer-input", Input).value = ""

    def set_controls(self, action_label: str, action_enabled: bool, hint_enabled: bool) -> None:
        action_button = self.query_one("#round-action-button", Button)
        hint_button = self.query_one("#hint-button", Button)

        action_button.label = action_label
        action_button.disabled = not action_enabled

        hint_button.disabled = not hint_enabled

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app = cast("ScriptureBaseballApp", self.app)
        if event.button.id == "round-action-button":
            answer_text = self.query_one("#answer-input", Input).value.strip()
            app.handle_round_action(answer_text)
        elif event.button.id == "hint-button":
            app.request_hint()
        elif event.button.id == "back-to-menu-button":
            app.return_to_menu()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "answer-input":
            return
        app = cast("ScriptureBaseballApp", self.app)
        app.handle_round_action(event.value.strip())

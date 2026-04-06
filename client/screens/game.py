from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual.containers import Container
from textual.widgets import Button, Input, Static

if TYPE_CHECKING:
    from client.app import ScriptureBaseballApp


class GamePanel(Container):
    def compose(self):
        yield Static("[bold green]Game In Progress[/bold green]", id="game-title")
        yield Static("", id="round-info")
        yield Static("", id="score-info")
        yield Static("", id="lives-info")
        yield Static("[bold cyan]Verse to Guess[/bold cyan]", id="prompt-label")
        yield Static("", id="prompt-info")
        yield Static("[dim]--------------------[/dim]", id="prompt-separator")
        yield Static("[bold magenta]Hint Verses[/bold magenta]", id="hint-label")
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
        round_progress: str,
        rounds_remaining: int | None,
        show_lives: bool,
    ) -> None:
        self.query_one("#round-info", Static).update(f"[bold]Round:[/bold] {round_progress}")
        self.query_one("#score-info", Static).update(f"[bold yellow]Points:[/bold yellow] {score}")
        lives_text = ""
        if show_lives:
            lives_text = f"[bold red]Lives:[/bold red] {lives_remaining if lives_remaining is not None else '--'}"
        self.query_one("#lives-info", Static).update(lives_text)
        if rounds_remaining is not None:
            self.query_one("#feedback-output", Static).update(
                f"[dim]Rounds remaining: {rounds_remaining}[/dim]"
            )

    def set_prompt(self, prompt_text: str) -> None:
        self.query_one("#prompt-info", Static).update(f"[bold cyan]{prompt_text}[/bold cyan]")

    def set_hint(self, hint_lines: list[str], target_index: int | None = None) -> None:
        if len(hint_lines) == 0:
            self.query_one("#hint-output", Static).update("[dim]No hints used yet.[/dim]")
            return

        colored_lines: list[str] = []
        for index, line in enumerate(hint_lines):
            if target_index is not None and index == target_index:
                colored_lines.append(f"[bold cyan]{line}[/bold cyan]")
            else:
                colored_lines.append(f"[magenta]{line}[/magenta]")

        self.query_one("#hint-output", Static).update("\n".join(colored_lines))

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

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
        yield Button("Submit Answer", id="submit-answer-button")
        yield Button("Get Hint", id="hint-button")
        yield Button("Next Round", id="next-round-button")
        yield Button("Back to Setup", id="back-to-setup-button")

    def set_round_state(
        self,
        round_number: int,
        score: int,
        lives_remaining: int | None,
        round_progress: str,
        rounds_remaining: int | None,
    ) -> None:
        self.query_one("#round-info", Static).update(f"[bold]Round:[/bold] {round_progress}")
        self.query_one("#score-info", Static).update(f"[bold yellow]Points:[/bold yellow] {score}")
        self.query_one("#lives-info", Static).update(
            f"[bold red]Lives:[/bold red] {lives_remaining if lives_remaining is not None else '--'}"
        )
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

    def set_controls(self, submit_enabled: bool, hint_enabled: bool, next_enabled: bool) -> None:
        submit_button = self.query_one("#submit-answer-button", Button)
        next_button = self.query_one("#next-round-button", Button)
        hint_button = self.query_one("#hint-button", Button)

        submit_button.disabled = not submit_enabled
        submit_button.display = submit_enabled

        next_button.disabled = not next_enabled
        next_button.display = next_enabled

        hint_button.disabled = not hint_enabled

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app = cast("ScriptureBaseballApp", self.app)
        if event.button.id == "submit-answer-button":
            answer_text = self.query_one("#answer-input", Input).value.strip()
            app.submit_answer(answer_text)
        elif event.button.id == "hint-button":
            app.request_hint()
        elif event.button.id == "next-round-button":
            app.next_round()
        elif event.button.id == "back-to-setup-button":
            app.return_to_setup()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "answer-input":
            return
        app = cast("ScriptureBaseballApp", self.app)
        app.submit_answer(event.value.strip())

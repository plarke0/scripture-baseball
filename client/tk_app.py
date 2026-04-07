from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable

from client.facade_server import FacadeServer
from client.scoring_service import ScoringService
from client.session_state import ClientSessionState
from client.ui_theme import TK_SIZES, configure_tk_theme
from shared.game import Game
from shared.request_classes import VerseRequest
from shared.response_classes import VerseResponse


class _HeadlessRoot:
    def after(self, _delay: int, callback):
        callback()
        return "headless-after"

    def after_cancel(self, _after_id: str) -> None:
        return

    def withdraw(self) -> None:
        return

    def mainloop(self) -> None:
        return


def _bind_dynamic_wrap(label: ttk.Label) -> None:
    def _on_resize(event: tk.Event) -> None:
        if event.width <= 1:
            return
        current = int(float(label.cget("wraplength")))
        if current != event.width:
            label.configure(wraplength=event.width)

    label.bind("<Configure>", _on_resize, add="+")


class TkLoginPanel(ttk.Frame):
    def __init__(
        self,
        parent: ttk.Frame,
        on_submit: Callable[[str, str], None],
        on_to_register: Callable[[], None],
    ) -> None:
        super().__init__(parent, padding=TK_SIZES["panel_padding"])
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)

        ttk.Label(self, text="Scripture Baseball", style="Section.TLabel").grid(
            row=0,
            column=1,
            sticky="ew",
            pady=(0, 12),
        )

        form = ttk.Frame(self)
        form.grid(row=1, column=1, sticky="ew")
        form.columnconfigure(0, weight=1)

        ttk.Label(form, text="Username").grid(row=0, column=0, sticky="w")
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(form, width=TK_SIZES["field_width"], textvariable=self.username_var)
        username_entry.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(form, text="Password").grid(row=2, column=0, sticky="w")
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(form, width=TK_SIZES["field_width"], textvariable=self.password_var, show="*")
        password_entry.grid(row=3, column=0, sticky="ew", pady=(0, 12))

        ttk.Button(
            form,
            text="Login",
            style="Accent.TButton",
            width=TK_SIZES["button_width"],
            command=lambda: on_submit(self.username_var.get().strip(), self.password_var.get()),
        ).grid(row=4, column=0, sticky="w", pady=(0, 8))
        ttk.Button(
            form,
            text="Need an account? Register",
            style="Secondary.TButton",
            width=TK_SIZES["button_width"],
            command=on_to_register,
        ).grid(
            row=5,
            column=0,
            sticky="w",
        )

        self.status_var = tk.StringVar(value="")
        status_label = ttk.Label(
            self,
            textvariable=self.status_var,
            wraplength=TK_SIZES["wrap_width"],
            justify="left",
            style="BodyMuted.TLabel",
        )
        status_label.grid(
            row=2,
            column=1,
            sticky="ew",
            pady=(12, 0),
        )
        _bind_dynamic_wrap(status_label)

        ttk.Frame(self).grid(row=3, column=1, sticky="nsew")

        username_entry.focus_set()
        username_entry.bind("<Return>", lambda _event: on_submit(self.username_var.get().strip(), self.password_var.get()))
        password_entry.bind("<Return>", lambda _event: on_submit(self.username_var.get().strip(), self.password_var.get()))

    def set_status(self, message: str) -> None:
        self.status_var.set(message)

    def clear_form(self) -> None:
        self.username_var.set("")
        self.password_var.set("")


class TkRegisterPanel(ttk.Frame):
    def __init__(
        self,
        parent: ttk.Frame,
        on_submit: Callable[[str, str, str], None],
        on_to_login: Callable[[], None],
    ) -> None:
        super().__init__(parent, padding=TK_SIZES["panel_padding"])
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)

        ttk.Label(self, text="Create Account", style="Section.TLabel").grid(
            row=0,
            column=1,
            sticky="ew",
            pady=(0, 12),
        )

        form = ttk.Frame(self)
        form.grid(row=1, column=1, sticky="ew")
        form.columnconfigure(0, weight=1)

        ttk.Label(form, text="Username").grid(row=0, column=0, sticky="w")
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(form, width=TK_SIZES["field_width"], textvariable=self.username_var)
        username_entry.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(form, text="Email").grid(row=2, column=0, sticky="w")
        self.email_var = tk.StringVar()
        email_entry = ttk.Entry(form, width=TK_SIZES["field_width"], textvariable=self.email_var)
        email_entry.grid(row=3, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(form, text="Password").grid(row=4, column=0, sticky="w")
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(form, width=TK_SIZES["field_width"], textvariable=self.password_var, show="*")
        password_entry.grid(row=5, column=0, sticky="ew", pady=(0, 12))

        ttk.Button(
            form,
            text="Register",
            style="Accent.TButton",
            width=TK_SIZES["button_width"],
            command=lambda: on_submit(
                self.username_var.get().strip(),
                self.email_var.get().strip(),
                self.password_var.get(),
            ),
        ).grid(row=6, column=0, sticky="w", pady=(0, 8))
        ttk.Button(
            form,
            text="Have an account? Login",
            style="Secondary.TButton",
            width=TK_SIZES["button_width"],
            command=on_to_login,
        ).grid(
            row=7,
            column=0,
            sticky="w",
        )

        self.status_var = tk.StringVar(value="")
        status_label = ttk.Label(
            self,
            textvariable=self.status_var,
            wraplength=TK_SIZES["wrap_width"],
            justify="left",
            style="BodyMuted.TLabel",
        )
        status_label.grid(
            row=2,
            column=1,
            sticky="ew",
            pady=(12, 0),
        )
        _bind_dynamic_wrap(status_label)

        ttk.Frame(self).grid(row=3, column=1, sticky="nsew")

        username_entry.focus_set()
        username_entry.bind(
            "<Return>",
            lambda _event: on_submit(
                self.username_var.get().strip(),
                self.email_var.get().strip(),
                self.password_var.get(),
            ),
        )
        email_entry.bind(
            "<Return>",
            lambda _event: on_submit(
                self.username_var.get().strip(),
                self.email_var.get().strip(),
                self.password_var.get(),
            ),
        )
        password_entry.bind(
            "<Return>",
            lambda _event: on_submit(
                self.username_var.get().strip(),
                self.email_var.get().strip(),
                self.password_var.get(),
            ),
        )

    def set_status(self, message: str) -> None:
        self.status_var.set(message)

    def clear_form(self) -> None:
        self.username_var.set("")
        self.email_var.set("")
        self.password_var.set("")


class TkSetupPanel(ttk.Frame):
    def __init__(
        self,
        parent: ttk.Frame,
        on_start_game: Callable[[str, str], None],
        on_view_leaderboards: Callable[[], None],
        on_logout: Callable[[], None],
    ) -> None:
        super().__init__(parent, padding=TK_SIZES["panel_padding"])
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)

        self._cached_mode_options: tuple[str, ...] | None = None
        self._cached_category_options: tuple[str, ...] | None = None
        self._mode_labels: dict[str, str] = {}
        self._category_labels: dict[str, str] = {}

        ttk.Label(self, text="Choose Mode and Category", style="Section.TLabel").grid(
            row=0,
            column=1,
            sticky="ew",
            pady=(0, 12),
        )

        form = ttk.Frame(self)
        form.grid(row=1, column=1, sticky="ew")
        form.columnconfigure(0, weight=1)

        ttk.Label(form, text="Mode").grid(row=0, column=0, sticky="w")
        self.mode_var = tk.StringVar(value="")
        self.mode_combo = ttk.Combobox(form, state="readonly", width=TK_SIZES["field_width"], textvariable=self.mode_var)
        self.mode_combo.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(form, text="Category").grid(row=2, column=0, sticky="w")
        self.category_var = tk.StringVar(value="")
        self.category_combo = ttk.Combobox(form, state="readonly", width=TK_SIZES["field_width"], textvariable=self.category_var)
        self.category_combo.grid(row=3, column=0, sticky="ew", pady=(0, 12))

        ttk.Button(
            form,
            text="Start Game",
            style="Accent.TButton",
            width=TK_SIZES["button_width"],
            command=lambda: on_start_game(
                self.get_selected_mode_id() or "",
                self.get_selected_category_id() or "",
            ),
        ).grid(row=4, column=0, sticky="w", pady=(0, 8))
        ttk.Button(
            form,
            text="View Leaderboards",
            style="Secondary.TButton",
            width=TK_SIZES["button_width"],
            command=on_view_leaderboards,
        ).grid(
            row=5,
            column=0,
            sticky="w",
            pady=(0, 8),
        )
        ttk.Button(form, text="Logout", style="Danger.TButton", command=on_logout).grid(
            row=6,
            column=0,
            sticky="w",
        )

        self.status_var = tk.StringVar(value="")
        status_label = ttk.Label(
            self,
            textvariable=self.status_var,
            wraplength=TK_SIZES["wrap_width"],
            justify="left",
            style="BodyMuted.TLabel",
        )
        status_label.grid(
            row=2,
            column=1,
            sticky="ew",
            pady=(12, 0),
        )
        _bind_dynamic_wrap(status_label)

        ttk.Frame(self).grid(row=3, column=1, sticky="nsew")

    def load_options(self, modes: list[dict], categories: list[dict]) -> None:
        mode_sig = tuple(sorted(str(mode["id"]) for mode in modes))
        category_sig = tuple(sorted(str(category["id"]) for category in categories))

        if mode_sig != self._cached_mode_options:
            self._mode_labels = {str(mode["name"]): str(mode["id"]) for mode in modes}
            mode_names = list(self._mode_labels.keys())
            self.mode_combo["values"] = mode_names
            self._cached_mode_options = mode_sig

        if category_sig != self._cached_category_options:
            self._category_labels = {str(category["name"]): str(category["id"]) for category in categories}
            category_names = list(self._category_labels.keys())
            self.category_combo["values"] = category_names
            self._cached_category_options = category_sig

        if modes:
            self.mode_var.set(str(modes[0]["name"]))
        if categories:
            self.category_var.set(str(categories[0]["name"]))

    def get_selected_mode_id(self) -> str | None:
        mode_name = self.mode_var.get().strip()
        if not mode_name:
            return None
        return self._mode_labels.get(mode_name)

    def get_selected_category_id(self) -> str | None:
        category_name = self.category_var.get().strip()
        if not category_name:
            return None
        return self._category_labels.get(category_name)

    def set_status(self, message: str) -> None:
        self.status_var.set(message)


class TkLeaderboardPanel(ttk.Frame):
    def __init__(
        self,
        parent: ttk.Frame,
        on_refresh: Callable[[str, str], None],
        on_back: Callable[[], None],
        on_filter_changed: Callable[[str, str], None],
    ) -> None:
        super().__init__(parent, padding=TK_SIZES["panel_padding"])
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)

        self._cached_mode_options: tuple[str, ...] | None = None
        self._cached_category_options: tuple[str, ...] | None = None
        self._mode_labels: dict[str, str] = {}
        self._category_labels: dict[str, str] = {}

        ttk.Label(self, text="Leaderboards", style="Section.TLabel").grid(
            row=0,
            column=1,
            sticky="ew",
            pady=(0, 12),
        )

        form = ttk.Frame(self)
        form.grid(row=1, column=1, sticky="ew")
        form.columnconfigure(0, weight=1)

        ttk.Label(form, text="Mode").grid(row=0, column=0, sticky="w")
        self.mode_var = tk.StringVar(value="")
        self.mode_combo = ttk.Combobox(form, state="readonly", width=TK_SIZES["field_width"], textvariable=self.mode_var)
        self.mode_combo.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(form, text="Category").grid(row=2, column=0, sticky="w")
        self.category_var = tk.StringVar(value="")
        self.category_combo = ttk.Combobox(form, state="readonly", width=TK_SIZES["field_width"], textvariable=self.category_var)
        self.category_combo.grid(row=3, column=0, sticky="ew", pady=(0, 12))

        ttk.Button(
            form,
            text="Refresh Leaderboard",
            style="Accent.TButton",
            width=TK_SIZES["button_width"],
            command=lambda: on_refresh(self.get_selected_category_id() or "", self.get_selected_mode_id() or ""),
        ).grid(row=4, column=0, sticky="w", pady=(0, 8))
        ttk.Button(form, text="Back to Menu", style="Secondary.TButton", width=TK_SIZES["button_width"], command=on_back).grid(
            row=5,
            column=0,
            sticky="w",
        )

        self.status_var = tk.StringVar(value="")
        status_label = ttk.Label(
            self,
            textvariable=self.status_var,
            wraplength=TK_SIZES["wrap_width"],
            justify="left",
            style="BodyMuted.TLabel",
        )
        status_label.grid(
            row=2,
            column=1,
            sticky="ew",
            pady=(12, 6),
        )
        _bind_dynamic_wrap(status_label)

        self.content_var = tk.StringVar(value="")
        content_label = ttk.Label(self, textvariable=self.content_var, wraplength=TK_SIZES["wrap_width"], justify="left")
        content_label.grid(
            row=3,
            column=1,
            sticky="nsew",
        )
        _bind_dynamic_wrap(content_label)

        self.mode_combo.bind(
            "<<ComboboxSelected>>",
            lambda _event: on_filter_changed(
                self.get_selected_category_id() or "",
                self.get_selected_mode_id() or "",
            ),
        )
        self.category_combo.bind(
            "<<ComboboxSelected>>",
            lambda _event: on_filter_changed(
                self.get_selected_category_id() or "",
                self.get_selected_mode_id() or "",
            ),
        )

    def load_filters(self, modes: list[dict], categories: list[dict]) -> None:
        mode_sig = tuple(sorted(str(mode["id"]) for mode in modes))
        category_sig = tuple(sorted(str(category["id"]) for category in categories))

        if mode_sig != self._cached_mode_options:
            self._mode_labels = {str(mode["name"]): str(mode["id"]) for mode in modes}
            mode_names = list(self._mode_labels.keys())
            self.mode_combo["values"] = mode_names
            self._cached_mode_options = mode_sig

        if category_sig != self._cached_category_options:
            self._category_labels = {str(category["name"]): str(category["id"]) for category in categories}
            category_names = list(self._category_labels.keys())
            self.category_combo["values"] = category_names
            self._cached_category_options = category_sig

        if modes:
            self.mode_var.set(str(modes[0]["name"]))
        if categories:
            self.category_var.set(str(categories[0]["name"]))

    def get_selected_mode_id(self) -> str | None:
        mode_name = self.mode_var.get().strip()
        if not mode_name:
            return None
        return self._mode_labels.get(mode_name)

    def get_selected_category_id(self) -> str | None:
        category_name = self.category_var.get().strip()
        if not category_name:
            return None
        return self._category_labels.get(category_name)

    def set_status(self, message: str) -> None:
        self.status_var.set(message)

    def set_rows(self, heading: str, rows: list[str]) -> None:
        content = heading
        if rows:
            content += "\n" + "\n".join(rows)
        self.content_var.set(content)


class TkGamePanel(ttk.Frame):
    def __init__(
        self,
        parent: ttk.Frame,
        on_round_action: Callable[[str], None],
        on_hint: Callable[[], None],
        on_back_to_menu: Callable[[], None],
    ) -> None:
        super().__init__(parent, padding=TK_SIZES["panel_padding"])
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(5, weight=1)
        self.rowconfigure(9, weight=1)

        ttk.Label(self, text="Game", style="Section.TLabel").grid(row=0, column=1, sticky="ew", pady=(0, 10))

        self.round_info_var = tk.StringVar(value="")
        self.score_info_var = tk.StringVar(value="")
        self.lives_info_var = tk.StringVar(value="")
        self.hints_info_var = tk.StringVar(value="")
        self.prompt_var = tk.StringVar(value="")
        self.hint_var = tk.StringVar(value="")
        self.feedback_var = tk.StringVar(value="")

        metrics = ttk.Frame(self)
        metrics.grid(row=1, column=1, sticky="ew", pady=(0, 8))
        for col in range(4):
            metrics.columnconfigure(col, weight=1)

        ttk.Label(metrics, textvariable=self.round_info_var).grid(row=0, column=0, sticky="w")
        ttk.Label(metrics, textvariable=self.score_info_var).grid(row=0, column=1, sticky="w")
        ttk.Label(metrics, textvariable=self.lives_info_var).grid(row=0, column=2, sticky="w")
        ttk.Label(metrics, textvariable=self.hints_info_var).grid(row=0, column=3, sticky="w")

        ttk.Label(self, text="Verse to Guess", style="BodyMuted.TLabel").grid(row=2, column=1, sticky="w")
        prompt_label = ttk.Label(self, textvariable=self.prompt_var, wraplength=TK_SIZES["wrap_width"], justify="left")
        prompt_label.grid(
            row=3,
            column=1,
            sticky="nsew",
            pady=(0, 8),
        )
        _bind_dynamic_wrap(prompt_label)

        self.hint_label = ttk.Label(self, text="Hint Verses", style="BodyMuted.TLabel")
        self.hint_label.grid(row=4, column=1, sticky="w")
        self.hint_output = ttk.Label(self, textvariable=self.hint_var, wraplength=TK_SIZES["wrap_width"], justify="left")
        self.hint_output.grid(row=5, column=1, sticky="nsew", pady=(0, 8))
        _bind_dynamic_wrap(self.hint_output)

        feedback_label = ttk.Label(self, textvariable=self.feedback_var, wraplength=TK_SIZES["wrap_width"], justify="left")
        feedback_label.grid(
            row=6,
            column=1,
            sticky="ew",
            pady=(0, 8),
        )
        _bind_dynamic_wrap(feedback_label)

        self.answer_var = tk.StringVar(value="")
        answer_entry = ttk.Entry(self, width=TK_SIZES["answer_width"], textvariable=self.answer_var)
        answer_entry.grid(row=7, column=1, sticky="ew", pady=(0, 8))

        actions = ttk.Frame(self)
        actions.grid(row=8, column=1, sticky="")

        self.action_button = ttk.Button(
            actions,
            text="Submit Answer",
            style="Accent.TButton",
            width=18,
            command=lambda: on_round_action(self.answer_var.get().strip()),
        )
        self.action_button.grid(row=0, column=0, sticky="", pady=(0, 8), padx=(0, 6))

        self.hint_button = ttk.Button(actions, text="Get Hint", style="Secondary.TButton", width=18, command=on_hint)
        self.hint_button.grid(row=0, column=1, sticky="", pady=(0, 8), padx=6)

        ttk.Button(actions, text="Back to Menu", style="Secondary.TButton", width=18, command=on_back_to_menu).grid(
            row=0,
            column=2,
            sticky="",
            pady=(0, 8),
            padx=(6, 0),
        )

        ttk.Frame(self).grid(row=9, column=1, sticky="nsew")

        answer_entry.bind("<Return>", lambda _event: on_round_action(self.answer_var.get().strip()))
        self.set_hint([], None)

    def set_round_state(
        self,
        _round_number: int,
        score: int,
        lives_remaining: int | None,
        hints_remaining: int | None,
        round_progress: str,
        is_endless: bool,
    ) -> None:
        self.round_info_var.set(f"Round: {round_progress}")
        self.score_info_var.set(f"Points: {score}")
        self.lives_info_var.set(f"Lives: {lives_remaining if lives_remaining is not None else '--'}" if is_endless else "")
        self.hints_info_var.set(f"Hints Remaining: {hints_remaining if hints_remaining is not None else '--'}" if is_endless else "")

    def set_prompt(self, prompt_text: str) -> None:
        self.prompt_var.set(prompt_text)

    def set_hint(self, hint_lines: list[str], target_index: int | None = None) -> None:
        if len(hint_lines) == 0:
            self.hint_label.grid_remove()
            self.hint_output.grid_remove()
            self.hint_var.set("")
            return

        self.hint_label.grid()
        self.hint_output.grid()
        lines: list[str] = []
        for index, line in enumerate(hint_lines):
            prefix = "> " if target_index is not None and index == target_index else ""
            lines.append(f"{prefix}{line}")
        self.hint_var.set("\n".join(lines))

    def set_feedback(self, feedback_text: str) -> None:
        self.feedback_var.set(feedback_text)

    def clear_answer(self) -> None:
        self.answer_var.set("")

    def set_controls(self, action_label: str, action_enabled: bool, hint_enabled: bool) -> None:
        self.action_button.configure(text=action_label)
        if action_enabled:
            self.action_button.state(["!disabled"])
        else:
            self.action_button.state(["disabled"])

        if hint_enabled:
            self.hint_button.state(["!disabled"])
        else:
            self.hint_button.state(["disabled"])


class TkResultsPanel(ttk.Frame):
    def __init__(
        self,
        parent: ttk.Frame,
        on_play_again: Callable[[], None],
        on_back_to_menu: Callable[[], None],
    ) -> None:
        super().__init__(parent, padding=TK_SIZES["panel_padding"])
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(5, weight=1)

        ttk.Label(self, text="Game Complete", style="Section.TLabel").grid(row=0, column=1, sticky="ew", pady=(0, 10))
        self.final_score_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.final_score_var).grid(row=1, column=1, sticky="ew")

        self.message_var = tk.StringVar(value="")
        message_label = ttk.Label(self, textvariable=self.message_var, wraplength=TK_SIZES["wrap_width"], justify="left")
        message_label.grid(
            row=2,
            column=1,
            sticky="nsew",
            pady=(8, 10),
        )
        _bind_dynamic_wrap(message_label)

        ttk.Button(self, text="Play Again", style="Accent.TButton", command=on_play_again).grid(
            row=3,
            column=1,
            sticky="w",
            pady=(0, 8),
        )
        ttk.Button(self, text="Back to Menu", style="Secondary.TButton", command=on_back_to_menu).grid(
            row=4,
            column=1,
            sticky="w",
        )

        ttk.Frame(self).grid(row=5, column=1, sticky="nsew")

    def set_results(self, final_score: int, message: str) -> None:
        self.final_score_var.set(f"Final Score: {final_score}")
        self.message_var.set(message)


class TkConfirmExitPanel(ttk.Frame):
    def __init__(
        self,
        parent: ttk.Frame,
        on_confirm: Callable[[], None],
        on_cancel: Callable[[], None],
    ) -> None:
        super().__init__(parent, padding=TK_SIZES["panel_padding"])
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(4, weight=1)

        ttk.Label(self, text="Leave Current Game?", style="Section.TLabel").grid(row=0, column=1, sticky="ew", pady=(0, 10))
        message_label = ttk.Label(
            self,
            text="If you leave now, your current score will be submitted and you will return to the menu.",
            wraplength=TK_SIZES["wrap_width"],
            justify="left",
        )
        message_label.grid(row=1, column=1, sticky="nsew", pady=(0, 10))
        _bind_dynamic_wrap(message_label)

        ttk.Button(self, text="Confirm Leave", style="Danger.TButton", command=on_confirm).grid(
            row=2,
            column=1,
            sticky="w",
            pady=(0, 8),
        )
        ttk.Button(self, text="Cancel", style="Secondary.TButton", command=on_cancel).grid(row=3, column=1, sticky="w")

        ttk.Frame(self).grid(row=4, column=1, sticky="nsew")


class TkScriptureBaseballApp:
    """Primary tkinter application shell for Scripture Baseball."""

    def __init__(self, enable_ui: bool = True) -> None:
        self.root: Any = tk.Tk() if enable_ui else _HeadlessRoot()
        if enable_ui:
            self.root.title("Scripture Baseball")
            self.root.geometry("1000x700")
            self.root.minsize(900, 620)
            configure_tk_theme(self.root)

        self.facade = FacadeServer()
        self.game = Game()
        self.session = ClientSessionState()
        self.login_panel: TkLoginPanel | None = None
        self.register_panel: TkRegisterPanel | None = None
        self.setup_panel: TkSetupPanel | None = None
        self.leaderboard_panel: TkLeaderboardPanel | None = None
        self.game_panel: TkGamePanel | None = None
        self.results_panel: TkResultsPanel | None = None
        self.confirm_exit_panel: TkConfirmExitPanel | None = None
        self._active_panel = "login"
        self._leaderboard_after_id: str | None = None
        self._leaderboard_debounce_delay_ms = 400

        self._panels: dict[str, ttk.Frame] = {}
        if enable_ui:
            self._build_shell()

    def _build_shell(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        container = ttk.Frame(self.root, padding=TK_SIZES["container_padding"])
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        title = ttk.Label(container, text="Scripture Baseball", style="Title.TLabel")
        title.grid(row=0, column=0, sticky="w", pady=(0, 10))

        panel_host = ttk.Frame(container)
        panel_host.grid(row=1, column=0, sticky="nsew")
        panel_host.columnconfigure(0, weight=1)
        panel_host.rowconfigure(0, weight=1)

        self.login_panel = TkLoginPanel(
            panel_host,
            on_submit=self.handle_login,
            on_to_register=self.show_register,
        )
        self.login_panel.grid(row=0, column=0, sticky="nsew")
        self._panels["login"] = self.login_panel

        self.register_panel = TkRegisterPanel(
            panel_host,
            on_submit=self.handle_register,
            on_to_login=self.show_login,
        )
        self.register_panel.grid(row=0, column=0, sticky="nsew")
        self._panels["register"] = self.register_panel

        self.setup_panel = TkSetupPanel(
            panel_host,
            on_start_game=self.start_game_flow,
            on_view_leaderboards=self.open_leaderboards,
            on_logout=self.handle_logout,
        )
        self.setup_panel.grid(row=0, column=0, sticky="nsew")
        self._panels["setup"] = self.setup_panel

        self.game_panel = TkGamePanel(
            panel_host,
            on_round_action=self.handle_round_action,
            on_hint=self.request_hint,
            on_back_to_menu=self.return_to_menu,
        )
        self.game_panel.grid(row=0, column=0, sticky="nsew")
        self._panels["game"] = self.game_panel

        self.leaderboard_panel = TkLeaderboardPanel(
            panel_host,
            on_refresh=self.refresh_leaderboard,
            on_back=self.return_to_setup,
            on_filter_changed=self.debounce_leaderboard_refresh,
        )
        self.leaderboard_panel.grid(row=0, column=0, sticky="nsew")
        self._panels["leaderboard"] = self.leaderboard_panel

        self.results_panel = TkResultsPanel(
            panel_host,
            on_play_again=self.start_new_game,
            on_back_to_menu=self.return_to_menu,
        )
        self.results_panel.grid(row=0, column=0, sticky="nsew")
        self._panels["results"] = self.results_panel

        self.confirm_exit_panel = TkConfirmExitPanel(
            panel_host,
            on_confirm=self.confirm_exit_game,
            on_cancel=self.cancel_exit_game,
        )
        self.confirm_exit_panel.grid(row=0, column=0, sticky="nsew")
        self._panels["confirm-exit"] = self.confirm_exit_panel

        self.show_panel("login")

    def show_panel(self, name: str) -> None:
        for panel_name, panel in self._panels.items():
            if panel_name == name:
                panel.tkraise()
        self._active_panel = name

    def show_login(self) -> None:
        if self.register_panel is not None:
            self.register_panel.set_status("")
        self.show_panel("login")

    def show_register(self) -> None:
        if self.login_panel is not None:
            self.login_panel.set_status("")
        self.show_panel("register")

    def handle_login(self, username: str, password: str) -> None:
        if self.login_panel is None:
            return

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

        self.session.auth_token = auth_token
        self.session.username = username
        self.login_panel.clear_form()
        self.login_panel.set_status("Login successful.")
        self._enter_setup()

    def handle_register(self, username: str, email: str, password: str) -> None:
        if self.register_panel is None:
            return

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

        self.session.auth_token = auth_token
        self.session.username = username
        self.register_panel.clear_form()
        self.register_panel.set_status("Registration successful.")
        self._enter_setup()

    def _enter_setup(self) -> None:
        self._refresh_setup_options()
        if self.setup_panel is not None:
            self.setup_panel.set_status("")
        self.show_panel("setup")

    def _refresh_setup_options(self) -> None:
        if self.setup_panel is None:
            return
        self.setup_panel.load_options(self.game.get_available_modes(), self.game.get_available_categories())

    def handle_logout(self) -> None:
        if self.session.auth_token:
            try:
                self.facade.logout_user(self.session.auth_token)
            except Exception:
                pass

        self.session = ClientSessionState()
        self.game = Game()
        self._refresh_setup_options()
        self.show_panel("login")
        if self.login_panel is not None:
            self.login_panel.set_status("Logged out.")

    def start_game_flow(self, mode_id: str, category_id: str) -> None:
        if self.setup_panel is None:
            return
        if not mode_id or not category_id:
            self.setup_panel.set_status("Select a mode and category before starting.")
            return

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
        self._start_round()

    def start_new_game(self) -> None:
        if self.session.auth_token is None or self.session.selected_mode_id is None or self.session.selected_category_id is None:
            self.show_panel("login")
            return
        self.game = Game()
        self.start_game_flow(self.session.selected_mode_id, self.session.selected_category_id)

    def return_to_setup(self) -> None:
        self._enter_setup()

    def return_to_menu(self) -> None:
        if self.session.auth_token is None:
            self.show_panel("login")
            return
        if self._active_panel == "game":
            self.show_panel("confirm-exit")
            return
        self._enter_setup()

    def confirm_exit_game(self) -> None:
        message = self._submit_current_score(finalize_message=False)
        self._enter_setup()
        if self.setup_panel is not None:
            self.setup_panel.set_status(message)

    def cancel_exit_game(self) -> None:
        self.show_panel("game")

    def open_leaderboards(self) -> None:
        if self.leaderboard_panel is None:
            return
        self.leaderboard_panel.load_filters(
            self.game.get_available_modes(),
            self.game.get_available_categories(),
        )
        self.leaderboard_panel.set_status("Loading leaderboard...")
        self.leaderboard_panel.set_rows("", [])
        self.show_panel("leaderboard")

        mode_id = self.leaderboard_panel.get_selected_mode_id()
        category_id = self.leaderboard_panel.get_selected_category_id()
        if mode_id is not None and category_id is not None:
            self.refresh_leaderboard(category_id, mode_id)

    def refresh_leaderboard(self, category_id: str, mode_id: str) -> None:
        if self.leaderboard_panel is None:
            return
        if not category_id or not mode_id:
            self.leaderboard_panel.set_status("Select a mode and category first.")
            return
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
            f"Top Scores ({category_name}: {mode_name})\nYour Highscore: {my_score.highscore}",
            rows,
        )
        self.leaderboard_panel.set_status("")

    def debounce_leaderboard_refresh(self, category_id: str, mode_id: str) -> None:
        if self.leaderboard_panel is None:
            return
        if not category_id or not mode_id:
            return

        if self._leaderboard_after_id is not None:
            self.root.after_cancel(self._leaderboard_after_id)

        self.session.leaderboard_request_id += 1
        request_id = self.session.leaderboard_request_id
        self.leaderboard_panel.set_status("Updating scores...")

        def _run_refresh() -> None:
            self._leaderboard_after_id = None
            if request_id != self.session.leaderboard_request_id:
                return
            self.refresh_leaderboard(category_id, mode_id)

        self._leaderboard_after_id = self.root.after(self._leaderboard_debounce_delay_ms, _run_refresh)

    def next_round(self) -> None:
        if self.game_panel is None:
            return
        if self.session.is_round_loading:
            self.game_panel.set_feedback("Selecting verse...")
            return
        if not self.session.round_submitted:
            self.game_panel.set_feedback("Submit an answer before continuing.")
            return
        if self.game.is_game_over():
            self._finish_game()
            return
        self._start_round()

    def handle_round_action(self, answer_text: str) -> None:
        if self.game_panel is None:
            return
        if self.session.is_round_loading:
            self.game_panel.set_feedback("Selecting verse...")
            return
        if self.session.round_submitted:
            self.next_round()
            return
        self.submit_answer(answer_text)

    def request_hint(self) -> None:
        if self.game_panel is None:
            return
        if self.session.is_round_loading:
            self.game_panel.set_feedback("Selecting verse...")
            return
        if self.session.round_submitted:
            if self.game.is_game_over():
                self.game_panel.set_feedback("Game is complete. Press End Game to view results.")
            else:
                self.game_panel.set_feedback("Round complete. Start the next round or end the game.")
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
        if self.game_panel is None:
            return
        if not answer_text:
            self.game_panel.set_feedback("Enter an answer before submitting.")
            return

        if self.session.round_submitted:
            if self.game.is_game_over():
                self.game_panel.set_feedback("Game is complete. Press End Game to view results.")
            else:
                self.game_panel.set_feedback("Round complete. Start the next round or end the game.")
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

    def _start_round(self) -> None:
        if self.game_panel is None:
            return
        if self.session.is_round_loading:
            return

        selected = self.game.start_round()
        self.session.current_round = self.game.get_round_number()
        self.session.current_target = selected
        self.session.hint_lines = []
        self.session.hint_target_index = None
        self.session.round_submitted = False
        self.session.feedback = "Selecting verse..."
        self.session.is_round_loading = True
        self.session.round_request_id += 1
        request_id = self.session.round_request_id

        self.show_panel("game")
        self.game_panel.set_hint([], None)
        self.game_panel.set_prompt("Selecting verse...")
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
            error_message = str(error)
            self.root.after(0, lambda: self._complete_round_fetch_error(request_id, error_message))
            return

        self.root.after(0, lambda: self._complete_round_fetch_success(request_id, verse_response))

    def _complete_round_fetch_success(self, request_id: int, verse_response: VerseResponse) -> None:
        if self.game_panel is None:
            return
        if request_id != self.session.round_request_id:
            return

        self.session.is_round_loading = False
        self.game.set_chapter_data(verse_response.chapter)
        self.session.feedback = ""
        self.game_panel.set_prompt(verse_response.verse)
        self.game_panel.set_feedback("")
        self._refresh_game_panel()

    def _complete_round_fetch_error(self, request_id: int, error_message: str) -> None:
        if self.game_panel is None:
            return
        if request_id != self.session.round_request_id:
            return

        self.session.is_round_loading = False
        self.session.feedback = f"Unable to load verse: {error_message}"
        self.game_panel.set_prompt("Verse unavailable")
        self.game_panel.set_feedback(self.session.feedback)
        self._refresh_game_panel()

    def _refresh_game_panel(self) -> None:
        if self.game_panel is None:
            return
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
        if self.game_panel is None:
            return
        if self.session.is_round_loading:
            self.game_panel.set_controls("Selecting Verse...", False, False)
            return

        if self.session.round_submitted:
            if self.game.is_game_over():
                self.game_panel.set_controls("End Game", True, False)
                return
            self.game_panel.set_controls("Next Round", True, False)
            return

        self.game_panel.set_controls("Submit Answer", True, self.game.get_hints_remaining() != 0)

    def _finish_game(self) -> None:
        if self.results_panel is None:
            return
        message = self._submit_current_score(finalize_message=True)
        self.results_panel.set_results(self.session.final_score, message)
        self.show_panel("results")

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
                return f"Completed {rounds_played} rounds in {mode_name}. Score submitted successfully."
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

    @staticmethod
    def _build_score_category_id(category_id: str, mode_id: str) -> str:
        return f"{category_id}-{mode_id}"

    def run(self) -> None:
        self.root.mainloop()

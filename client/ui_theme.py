from __future__ import annotations

import tkinter as tk
from tkinter import ttk

# Increase/decrease this one value to scale the whole Tk UI.
UI_SCALE = 1.3


def _scaled(value: int) -> int:
    return max(1, int(round(value * UI_SCALE)))

# Change colors here to update UI text color styling across panels.
UI_COLORS: dict[str, str] = {
    "title": "green",
    "heading": "cyan",
    "section_title": "magenta",
    "score_label": "yellow",
    "lives_label": "red",
    "hint_label": "magenta",
    "hint": "magenta",
    "selected_verse": "cyan",
    "feedback_success": "green",
    "feedback_warning": "yellow",
    "feedback_error": "red",
    "loading_state": "yellow",
    "separator": "",
    "supporting_text": "",
}

# Tkinter UI tokens used by the active desktop client.
TK_COLORS: dict[str, str] = {
    "bg": "#f8f3e8",
    "panel": "#fffdf8",
    "surface": "#efe5cf",
    "text": "#2f2616",
    "muted_text": "#8a7d6a",
    "accent": "#1f5c3f",
    "accent_active": "#184a33",
    "secondary": "#d7c7a3",
    "secondary_active": "#c6b48f",
    "danger": "#8a2e2e",
    "danger_active": "#702424",
    "border": "#cabd9d",
}

TK_FONTS: dict[str, tuple[str, int] | tuple[str, int, str]] = {
    "title": ("Cambria", _scaled(18), "bold"),
    "section": ("Cambria", _scaled(14), "bold"),
    "body": ("Segoe UI", _scaled(10)),
    "body_bold": ("Segoe UI", _scaled(10), "bold"),
}

TK_SIZES: dict[str, int] = {
    "panel_padding": _scaled(22),
    "container_padding": _scaled(16),
    "field_width": _scaled(38),
    "answer_width": _scaled(44),
    "button_width": _scaled(24),
    "wrap_width": _scaled(640),
    "button_padding_x": _scaled(14),
    "button_padding_y": _scaled(8),
}


def configure_tk_theme(root: tk.Tk) -> None:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    root.configure(background=TK_COLORS["bg"])
    root.option_add("*Font", TK_FONTS["body"])

    style.configure("TFrame", background=TK_COLORS["bg"])
    style.configure("TLabel", background=TK_COLORS["bg"], foreground=TK_COLORS["text"])
    style.configure("Title.TLabel", font=TK_FONTS["title"], foreground=TK_COLORS["text"])
    style.configure("Section.TLabel", font=TK_FONTS["section"], foreground=TK_COLORS["text"])
    style.configure("BodyMuted.TLabel", foreground=TK_COLORS["muted_text"])
    style.configure("Feedback.TLabel", font=TK_FONTS["body_bold"], foreground=TK_COLORS["text"])
    style.configure(
        "TEntry",
        fieldbackground=TK_COLORS["panel"],
        foreground=TK_COLORS["text"],
        bordercolor=TK_COLORS["border"],
        insertcolor=TK_COLORS["text"],
    )
    style.configure(
        "Placeholder.TEntry",
        fieldbackground=TK_COLORS["panel"],
        foreground=TK_COLORS["muted_text"],
        bordercolor=TK_COLORS["border"],
        insertcolor=TK_COLORS["muted_text"],
    )
    style.configure(
        "TCombobox",
        fieldbackground=TK_COLORS["panel"],
        foreground=TK_COLORS["text"],
        bordercolor=TK_COLORS["border"],
        arrowsize=14,
    )

    style.configure(
        "Accent.TButton",
        background=TK_COLORS["accent"],
        foreground="#ffffff",
        bordercolor=TK_COLORS["accent"],
        lightcolor=TK_COLORS["accent"],
        darkcolor=TK_COLORS["accent"],
        padding=(TK_SIZES["button_padding_x"], TK_SIZES["button_padding_y"]),
        font=TK_FONTS["body_bold"],
    )
    style.map(
        "Accent.TButton",
        background=[("active", TK_COLORS["accent_active"]), ("disabled", "#879487")],
        foreground=[("disabled", "#f4f4f4")],
    )

    style.configure(
        "Secondary.TButton",
        background=TK_COLORS["secondary"],
        foreground=TK_COLORS["text"],
        bordercolor=TK_COLORS["border"],
        lightcolor=TK_COLORS["secondary"],
        darkcolor=TK_COLORS["secondary"],
        padding=(TK_SIZES["button_padding_x"], TK_SIZES["button_padding_y"]),
        font=TK_FONTS["body_bold"],
    )
    style.map(
        "Secondary.TButton",
        background=[("active", TK_COLORS["secondary_active"]), ("disabled", "#ddd7cb")],
        foreground=[("disabled", "#7c7568")],
    )

    style.configure(
        "Danger.TButton",
        background=TK_COLORS["danger"],
        foreground="#ffffff",
        bordercolor=TK_COLORS["danger"],
        lightcolor=TK_COLORS["danger"],
        darkcolor=TK_COLORS["danger"],
        padding=(TK_SIZES["button_padding_x"], TK_SIZES["button_padding_y"]),
        font=TK_FONTS["body_bold"],
    )
    style.map(
        "Danger.TButton",
        background=[("active", TK_COLORS["danger_active"]), ("disabled", "#a18686")],
        foreground=[("disabled", "#f4f4f4")],
    )


def rich_text(text: str, theme_key: str, *, bold: bool = False, dim: bool = False) -> str:
    color = UI_COLORS.get(theme_key, theme_key)
    style_parts: list[str] = []
    if bold:
        style_parts.append("bold")
    if dim:
        style_parts.append("dim")
    if color:
        style_parts.append(color)

    style = " ".join(style_parts) if style_parts else "white"
    return f"[{style}]{text}[/{style}]"

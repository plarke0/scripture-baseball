from __future__ import annotations

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

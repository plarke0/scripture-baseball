from __future__ import annotations

from dataclasses import dataclass, field

from shared.request_classes import VerseRequest


@dataclass
class ClientSessionState:
    auth_token: str | None = None
    username: str | None = None
    selected_mode_id: str | None = None
    selected_category_id: str | None = None
    current_round: int = 0
    final_score: int = 0
    current_target: VerseRequest | None = None
    chapter_verses: list[str] = field(default_factory=list)
    hint_lines: list[str] = field(default_factory=list)
    hint_target_index: int | None = None
    round_submitted: bool = False
    pending_end_game_confirmation: bool = False
    feedback: str = ""

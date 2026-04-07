from __future__ import annotations

from typing import Callable


StyleFunc = Callable[[str, str], str]


def identity_style(text: str, _theme_key: str) -> str:
    return text


class ScoringService:
    @staticmethod
    def score_answer(
        closeness: dict,
        scoring_config: dict,
        category_metrics: dict,
        selected_mode_id: str | None,
        hints_used_this_round: int,
    ) -> int:
        max_round_points: int = int(scoring_config["max_round_points"])
        tiers: dict = scoring_config["tiers"]

        if closeness.get("is_exact"):
            base_points = max_round_points
        else:
            unit = str(closeness.get("unit", "book"))
            tier = tiers.get(unit)
            if not isinstance(tier, dict):
                return 0

            max_offsets = {
                "verse": max(int(category_metrics["verse_count"]) - 1, 1),
                "chapter": max(int(category_metrics["chapter_count"]) - 1, 1),
                "book": max(int(category_metrics["book_count"]) - 1, 1),
            }
            absolute_offset = int(closeness.get("absolute_offset", 0))
            normalized = min(max(absolute_offset / max_offsets[unit], 0.0), 1.0)

            tier_min = int(tier["min"])
            tier_max = int(tier["max"])
            span = tier_max - tier_min
            base_points = int(round(tier_max - (span * normalized)))

        if selected_mode_id != "endless" and hints_used_this_round > 0:
            multiplier = float(scoring_config["finite_hint_multiplier"])
            base_points = int(round(base_points * multiplier))

        return max(0, min(base_points, max_round_points))

    @staticmethod
    def format_distance_phrase(closeness: dict) -> str:
        unit = str(closeness.get("unit", "book"))
        absolute_offset = int(closeness.get("absolute_offset", 0))

        unit_label = unit if absolute_offset == 1 else f"{unit}s"
        return f"{absolute_offset} {unit_label} away"

    @staticmethod
    def format_submission_feedback(
        closeness: dict,
        points: int,
        life_lost: bool,
        selected_mode_id: str | None,
        hints_used_this_round: int,
        scoring_config: dict,
        correct_answer: str,
        style: StyleFunc = identity_style,
    ) -> str:
        context_notes: list[str] = []
        points_phrase = f"You earned +{points} points this round."

        if selected_mode_id != "endless" and hints_used_this_round > 0:
            multiplier = float(scoring_config["finite_hint_multiplier"])
            penalty_percent = max(0.0, (1.0 - multiplier) * 100.0)
            if penalty_percent.is_integer():
                penalty_display = str(int(penalty_percent))
            else:
                penalty_display = f"{penalty_percent:.1f}"

            context_notes.append(f"Hint used: {penalty_display}% point reduction")
            points_phrase = f"You earned +{points} points this round after the hint reduction."
        if life_lost:
            context_notes.append("life lost")

        notes_text = ""
        if len(context_notes) > 0:
            notes = "(" + "; ".join(context_notes) + ")"
            notes_text = " " + style(notes, "supporting_text")

        if closeness.get("is_exact"):
            success_text = style("Great guess!", "feedback_success")
            return (
                f"{success_text} Correct answer: {correct_answer}. "
                f"{points_phrase}{notes_text}"
            )

        distance_phrase = ScoringService.format_distance_phrase(closeness)
        warning_text = style("Close, but not exact.", "feedback_warning")
        return (
            f"{warning_text} Correct answer: {correct_answer}. "
            f"You were {distance_phrase}. {points_phrase}{notes_text}"
        )
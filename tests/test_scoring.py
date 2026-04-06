import unittest

from client.app import ScriptureBaseballApp


class TestScoring(unittest.TestCase):
    def _build_app(self, mode_id: str, category_id: str) -> ScriptureBaseballApp:
        app = ScriptureBaseballApp()
        app.game.select_mode(mode_id)
        app.game.select_category(category_id)
        app.game.start_game()
        app.session.selected_mode_id = mode_id
        app.session.selected_category_id = category_id
        return app

    def test_exact_finite_no_hint_gets_max_round_points(self) -> None:
        app = self._build_app("finite_5", "new_testament")

        points = app._score_answer({"is_exact": True, "unit": "verse", "absolute_offset": 0})

        self.assertEqual(points, 1000)

    def test_exact_finite_with_hint_gets_half_points(self) -> None:
        app = self._build_app("finite_5", "new_testament")
        app.game._hints_used_this_round = 1

        points = app._score_answer({"is_exact": True, "unit": "verse", "absolute_offset": 0})

        self.assertEqual(points, 500)

    def test_tier_ordering_descends_by_unit(self) -> None:
        app = self._build_app("finite_5", "new_testament")

        verse_points = app._score_answer({"is_exact": False, "unit": "verse", "absolute_offset": 1})
        chapter_points = app._score_answer({"is_exact": False, "unit": "chapter", "absolute_offset": 1})
        book_points = app._score_answer({"is_exact": False, "unit": "book", "absolute_offset": 1})

        self.assertGreater(verse_points, chapter_points)
        self.assertGreater(chapter_points, book_points)

    def test_larger_category_allows_higher_points_for_same_offset(self) -> None:
        all_scripture_app = self._build_app("finite_5", "all_scripture")
        gospels_app = self._build_app("finite_5", "gospels")

        closeness = {"is_exact": False, "unit": "book", "absolute_offset": 2}
        all_points = all_scripture_app._score_answer(closeness)
        gospel_points = gospels_app._score_answer(closeness)

        self.assertGreaterEqual(all_points, gospel_points)

    def test_leaderboard_key_uses_category_and_mode(self) -> None:
        self.assertEqual(
            ScriptureBaseballApp._build_score_category_id("new_testament", "finite_5"),
            "new_testament-finite_5",
        )

    def test_distance_phrase_is_human_readable(self) -> None:
        app = self._build_app("finite_5", "new_testament")

        phrase = app._format_distance_phrase({"unit": "chapter", "absolute_offset": 2, "offset": -2})

        self.assertIn("2 chapters away", phrase)
        self.assertNotIn("target", phrase)

    def test_submission_summary_includes_penalty_note_when_hint_used(self) -> None:
        app = self._build_app("finite_5", "new_testament")
        app.game._hints_used_this_round = 1
        app.game.get_correct_answer = lambda: "Matthew 1:1"
        app.game.get_final_score = lambda: 500

        summary = app._format_submission_feedback(
            {"is_exact": True, "unit": "verse", "absolute_offset": 0, "offset": 0},
            500,
            False,
            None,
        )

        self.assertIn("Great guess", summary)
        self.assertIn("after the hint reduction", summary)
        self.assertIn("50% point reduction", summary)
        self.assertIn("+500 points", summary)

    def test_submission_summary_includes_life_loss_note(self) -> None:
        app = self._build_app("endless", "new_testament")
        app.game.get_correct_answer = lambda: "Luke 2:10"
        app.game.get_final_score = lambda: 120

        summary = app._format_submission_feedback(
            {"is_exact": False, "unit": "book", "absolute_offset": 3, "offset": 3},
            20,
            True,
            2,
        )

        self.assertIn("Close, but not exact", summary)
        self.assertIn("life lost", summary)
        self.assertNotIn("lives remaining", summary)


if __name__ == "__main__":
    unittest.main()

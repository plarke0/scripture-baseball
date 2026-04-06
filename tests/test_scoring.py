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


if __name__ == "__main__":
    unittest.main()

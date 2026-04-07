import unittest

from shared.game import Game


class TestGameModes(unittest.TestCase):
	def test_mode_and_category_selection(self) -> None:
		game = Game()
		mode = game.select_mode("finite_5")
		category = game.select_category("gospels")
		game.start_game()
		selected = game.start_round()

		self.assertEqual(mode["id"], "finite_5")
		self.assertEqual(category["id"], "gospels")
		self.assertEqual(game.get_round_number(), 1)
		self.assertEqual(game.get_rounds_remaining(), 4)
		self.assertEqual(selected.volume, "newtestament")
		self.assertIn(selected.book, {"matthew", "mark", "luke", "john"})

	def test_available_dropdown_sources_are_cached_safely(self) -> None:
		game = Game()

		first_modes = game.get_available_modes()
		first_categories = game.get_available_categories()
		first_modes.append({"id": "temporary", "name": "Temporary"})
		first_categories.clear()

		second_modes = game.get_available_modes()
		second_categories = game.get_available_categories()

		self.assertNotIn({"id": "temporary", "name": "Temporary"}, second_modes)
		self.assertGreater(len(second_modes), 0)
		self.assertGreater(len(second_categories), 0)

	def test_endless_life_loss_on_wrong_book(self) -> None:
		game = Game()
		game.select_mode("endless")
		game.select_category("new_testament")
		game.start_game()
		selected = game.start_round()
		volume = game._volumes_by_id[selected.volume]

		available_book_ids = ["matthew", "mark", "luke", "john", "acts", "romans"]
		wrong_book_id = next(book_id for book_id in available_book_ids if book_id != selected.book)
		wrong_book_name = volume.get_book_name(wrong_book_id)
		game.set_chapter_data([f"verse {index}" for index in range(1, 200)])
		result = game.submit_answer(f"{wrong_book_name} 1:1")

		self.assertTrue(result["life_lost"])
		self.assertEqual(result["closeness"]["unit"], "book")
		self.assertEqual(game.get_lives_remaining(), 2)

	def test_finite_hint_limit(self) -> None:
		game = Game()
		game.select_mode("finite_5")
		game.select_category("new_testament")
		game.start_game()
		game.start_round()
		game.set_chapter_data([f"verse {index}" for index in range(1, 200)])

		first_hint = game.get_hint()
		self.assertEqual(len(first_hint["lines"]), 3)
		self.assertIn("target_index", first_hint)
		self.assertEqual(game.get_hints_remaining(), 0)
		with self.assertRaises(ValueError):
			game.get_hint()

	def test_final_score_accumulates(self) -> None:
		game = Game()
		self.assertEqual(game.get_final_score(), 0)
		self.assertEqual(game.add_score(1000), 1000)
		self.assertEqual(game.add_score(250), 1250)
		self.assertEqual(game.get_final_score(), 1250)

	def test_guess_from_different_volume_in_category_is_supported(self) -> None:
		game = Game()
		game.select_mode("finite_5")
		game.select_category("bible")
		game.start_game()
		selected = game.start_round()

		if selected.volume == "newtestament":
			guess = "Genesis 1:1"
		elif selected.volume == "oldtestament":
			guess = "Matthew 1:1"
		else:
			raise AssertionError(f"Unexpected volume for bible category: {selected.volume}")

		result = game.submit_answer(guess)
		self.assertIn("closeness", result)
		self.assertEqual(result["closeness"]["unit"], "book")


if __name__ == "__main__":
	unittest.main()

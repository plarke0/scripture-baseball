import json
import random
import re
from pathlib import Path
from typing import Any, Protocol

from shared.request_classes import VerseRequest
from shared.volume import Volume


class RandomSource(Protocol):
	def randint(self, a: int, b: int) -> int:
		...


class Game:
	def __init__(
		self,
		active_volumes_path: str = "active_volumes",
		game_settings_path: str = "game_settings.json",
		scripture_data_dir: str = "shared/scripture_data",
		rng: RandomSource | None = None,
	) -> None:
		self._scripture_data_dir: Path = Path(scripture_data_dir)
		self._active_volumes_path: Path = Path(active_volumes_path)
		self._game_settings_path: Path = Path(game_settings_path)
		self._rng: RandomSource = rng if rng is not None else random.Random()

		self._volumes_by_id: dict[str, Volume] = self._load_active_volumes()
		self._modes_by_id: dict[str, dict[str, Any]] = {}
		self._categories_by_id: dict[str, dict[str, Any]] = {}
		self._scoring_config: dict[str, Any] = {}
		self._load_game_settings()
		self._available_modes: tuple[dict[str, Any], ...] = tuple(self._modes_by_id.values())
		self._available_categories: tuple[dict[str, Any], ...] = tuple(self._categories_by_id.values())

		self._selected_mode_id: str | None = None
		self._selected_category_id: str | None = None
		self._selected_mode: dict[str, Any] | None = None
		self._selected_category: dict[str, Any] | None = None
		self._game_started: bool = False
		self._game_over: bool = False

		self._score: int = 0
		self._round_number: int = 0
		self._rounds_remaining: int | None = None
		self._lives_remaining: int | None = None
		self._endless_hints_remaining: int | None = None
		self._hints_used_this_round: int = 0

		self._selected_verse: VerseRequest | None = None
		self._selected_book_name: str | None = None
		self._selected_volume_id: str | None = None
		self._chapter_data: dict | list | None = None
		self._last_closeness: dict | None = None
		self._last_life_lost: bool = False

	def get_available_volume_ids(self) -> list[str]:
		return list(self._volumes_by_id.keys())

	def get_available_modes(self) -> list[dict[str, Any]]:
		return list(self._available_modes)

	def get_available_categories(self) -> list[dict[str, Any]]:
		return list(self._available_categories)

	def get_round_number(self) -> int:
		return self._round_number

	def select_mode(self, mode_id: str) -> dict[str, Any]:
		mode: dict[str, Any] = self._get_mode(mode_id)
		self._selected_mode_id = mode["id"]
		self._selected_mode = mode
		self._game_started = False
		self._reset_round_state()
		return dict(mode)

	def select_category(self, category_id: str) -> dict[str, Any]:
		category: dict[str, Any] = self._get_category(category_id)
		self._selected_category_id = category["id"]
		self._selected_category = category
		self._game_started = False
		self._reset_round_state()
		return dict(category)

	def start_game(self) -> None:
		mode: dict[str, Any] = self._require_selected_mode()
		self._require_selected_category()

		self._score = 0
		self._round_number = 0
		self._game_started = True
		self._game_over = False
		self._rounds_remaining = mode.get("rounds")
		self._lives_remaining = mode.get("lives")
		self._endless_hints_remaining = mode.get("hints")
		self._hints_used_this_round = 0
		self._reset_round_state(reset_score=False)

	def start_round(self) -> VerseRequest:
		if not self._game_started:
			self.start_game()

		if self._game_over:
			raise ValueError("Game is over")

		mode: dict[str, Any] = self._require_selected_mode()
		if mode["type"] == "finite" and self._rounds_remaining is not None and self._rounds_remaining <= 0:
			self._game_over = True
			raise ValueError("No rounds remaining")

		selected: VerseRequest = self._draw_target_from_selected_category()
		self._round_number += 1
		self._chapter_data = None
		self._last_closeness = None
		self._last_life_lost = False
		self._hints_used_this_round = 0

		if mode["type"] == "finite" and self._rounds_remaining is not None:
			self._rounds_remaining -= 1

		return selected

	def select_random_target(self, volume_id: str, start_book: str, end_book: str) -> VerseRequest:
		volume: Volume = self._get_volume(volume_id)
		selected: VerseRequest = volume.get_random_verse_between_books(start_book, end_book)

		self._selected_verse = selected
		self._selected_book_name = volume.get_book_name(selected.book)
		self._selected_volume_id = volume.volume_id
		self._chapter_data = None
		self._last_closeness = None
		self._last_life_lost = False
		self._round_number += 1
		return selected

	def set_chapter_data(self, chapter_data: dict | list) -> None:
		if not isinstance(chapter_data, (dict, list)):
			raise ValueError("Chapter data must be a dict or list")
		self._chapter_data = chapter_data

	def submit_answer(self, answer_text: str) -> dict:
		if self._selected_verse is None:
			raise ValueError("No active selected verse for this round")

		parsed_answer: dict[str, Any] = self.parse_answer(answer_text)
		closeness: dict[str, Any] = self.get_answer_closeness(
			self._selected_verse.volume,
			parsed_answer["book_name"],
			parsed_answer["chapter"],
			parsed_answer["verse"],
		)

		life_lost: bool = False
		mode: dict[str, Any] | None = self._selected_mode
		if mode is not None and mode["type"] == "endless" and closeness["unit"] != "verse":
			life_lost = True
			if self._lives_remaining is not None:
				self._lives_remaining -= 1
				if self._lives_remaining <= 0:
					self._game_over = True

		if mode is not None and mode["type"] == "finite" and self._rounds_remaining == 0:
			self._game_over = True

		self._last_closeness = closeness
		self._last_life_lost = life_lost

		return {
			"parsed_answer": parsed_answer,
			"closeness": closeness,
			"life_lost": life_lost,
			"lives_remaining": self._lives_remaining,
			"game_over": self._game_over,
		}

	def add_score(self, points: int) -> int:
		if not isinstance(points, int):
			raise ValueError("points must be an integer")
		self._score += points
		return self._score

	def get_final_score(self) -> int:
		return self._score

	def get_hints_used_this_round(self) -> int:
		return self._hints_used_this_round

	def get_scoring_config(self) -> dict[str, Any]:
		return dict(self._scoring_config)

	def get_selected_category_metrics(self) -> dict[str, int]:
		category: dict[str, Any] = self._require_selected_category()
		book_count: int = 0
		total_chapters: int = 0
		total_verses: int = 0

		for volume_entry in category["volumes"]:
			volume_id: str = volume_entry["id"]
			volume: Volume = self._get_volume(volume_id)
			book_ids: list[str] = volume.get_all_book_ids()
			if volume_entry.get("book_ids") is not None:
				book_ids = list(volume_entry["book_ids"])

			book_count += len(book_ids)
			total_chapters += volume.get_total_chapters_for_book_ids(book_ids)
			total_verses += volume.get_total_verses_for_book_ids(book_ids)

		return {
			"book_count": book_count,
			"chapter_count": total_chapters,
			"verse_count": total_verses,
		}

	def get_answer_closeness(
		self,
		volume_id: str,
		guess_book_name: str,
		guess_chapter: int,
		guess_verse: int,
	) -> dict[str, Any]:
		if self._selected_verse is None or self._selected_book_name is None or self._selected_volume_id is None:
			raise ValueError("No active selected verse for this round")
		if self._selected_verse.volume != volume_id:
			raise ValueError("Selected verse is not in the requested volume")

		guess_volume_id, canonical_guess_book_name = self._resolve_guess_in_selected_category(
			guess_book_name,
			guess_chapter,
			guess_verse,
		)

		target_volume_id: str = self._selected_volume_id
		target_book_name: str = self._selected_book_name
		target_chapter: int = self._selected_verse.chapter
		target_verse: int = self._selected_verse.verse

		if (
			guess_volume_id == target_volume_id
			and canonical_guess_book_name == target_book_name
			and guess_chapter == target_chapter
			and guess_verse == target_verse
		):
			return {"is_exact": True, "unit": "verse", "offset": 0, "absolute_offset": 0}

		if guess_volume_id == target_volume_id and canonical_guess_book_name == target_book_name and guess_chapter == target_chapter:
			offset: int = target_verse - guess_verse
			return {"is_exact": False, "unit": "verse", "offset": offset, "absolute_offset": abs(offset)}

		if guess_volume_id == target_volume_id and canonical_guess_book_name == target_book_name:
			offset = target_chapter - guess_chapter
			return {"is_exact": False, "unit": "chapter", "offset": offset, "absolute_offset": abs(offset)}

		category_book_sequence: list[tuple[str, str]] = self._get_selected_category_book_sequence()
		target_book_index: int = self._find_category_book_index(
			category_book_sequence,
			target_volume_id,
			target_book_name,
		)
		guess_book_index: int = self._find_category_book_index(
			category_book_sequence,
			guess_volume_id,
			canonical_guess_book_name,
		)
		offset = target_book_index - guess_book_index
		return {"is_exact": False, "unit": "book", "offset": offset, "absolute_offset": abs(offset)}

	def _resolve_guess_in_selected_category(self, guess_book_name: str, guess_chapter: int, guess_verse: int) -> tuple[str, str]:
		category: dict[str, Any] = self._require_selected_category()
		for volume_entry in category["volumes"]:
			volume_id: str = volume_entry["id"]
			volume: Volume = self._get_volume(volume_id)

			try:
				canonical_book_name: str = volume.resolve_book_name(guess_book_name)
			except ValueError:
				continue

			book_ids: list[str] = volume_entry["book_ids"] if volume_entry["book_ids"] is not None else volume.get_all_book_ids()
			canonical_book_id: str = volume.get_book_id(canonical_book_name)
			if canonical_book_id not in book_ids:
				continue

			volume.validate_verse_reference(canonical_book_name, guess_chapter, guess_verse)
			return (volume_id, canonical_book_name)

		raise ValueError(f"Unknown book in selected category: {guess_book_name.strip()}")

	def _get_selected_category_book_sequence(self) -> list[tuple[str, str]]:
		category: dict[str, Any] = self._require_selected_category()
		ordered_books: list[tuple[str, str]] = []

		for volume_entry in category["volumes"]:
			volume_id: str = volume_entry["id"]
			volume: Volume = self._get_volume(volume_id)
			book_ids: list[str] = volume_entry["book_ids"] if volume_entry["book_ids"] is not None else volume.get_all_book_ids()
			for book_id in book_ids:
				ordered_books.append((volume_id, volume.get_book_name(book_id)))

		return ordered_books

	@staticmethod
	def _find_category_book_index(
		category_book_sequence: list[tuple[str, str]],
		volume_id: str,
		book_name: str,
	) -> int:
		for index, (candidate_volume_id, candidate_book_name) in enumerate(category_book_sequence):
			if candidate_volume_id == volume_id and candidate_book_name == book_name:
				return index
		raise ValueError(f"Book not found in selected category order: {volume_id}:{book_name}")

	def get_correct_answer(self) -> str:
		if self._selected_verse is None or self._selected_book_name is None:
			raise ValueError("No active selected verse for this round")
		return f"{self._selected_book_name} {self._selected_verse.chapter}:{self._selected_verse.verse}"

	def get_hint(self) -> dict[str, Any]:
		if self._selected_verse is None:
			raise ValueError("No active selected verse for this round")
		if self._chapter_data is None:
			raise ValueError("No chapter data set for this round")

		mode: dict[str, Any] | None = self._selected_mode
		if mode is not None and mode["type"] == "endless":
			if self._hints_used_this_round == 0:
				if self._endless_hints_remaining is None or self._endless_hints_remaining <= 0:
					raise ValueError("No hints remaining")
		elif mode is not None and mode["type"] == "finite":
			if self._hints_used_this_round >= mode.get("hints_per_round", 1):
				raise ValueError("No hints remaining for this round")

		verses: list[str] = self._extract_chapter_verses(self._chapter_data)
		if len(verses) == 0:
			raise ValueError("Chapter data does not include verse text")

		target_index: int = self._selected_verse.verse - 1
		if target_index < 0 or target_index >= len(verses):
			raise ValueError("Selected verse is out of bounds for current chapter data")

		if mode is not None and mode["type"] == "endless":
			if self._hints_used_this_round == 0:
				if self._endless_hints_remaining is None:
					raise ValueError("No hints remaining")
				self._endless_hints_remaining -= 1
			self._hints_used_this_round = 1
		elif mode is not None and mode["type"] == "finite":
			self._hints_used_this_round += 1

		if len(verses) <= 3:
			return {"lines": verses, "target_index": target_index}
		if target_index == 0:
			return {"lines": verses[0:3], "target_index": 0}
		if target_index == len(verses) - 1:
			return {"lines": verses[len(verses) - 3:len(verses)], "target_index": 2}
		return {"lines": verses[target_index - 1:target_index + 2], "target_index": 1}

	def get_round_state(self) -> dict[str, Any]:
		return {
			"mode_id": self._selected_mode_id,
			"category_id": self._selected_category_id,
			"round_number": self._round_number,
			"rounds_remaining": self._rounds_remaining,
			"lives_remaining": self._lives_remaining,
			"hints_remaining": self.get_hints_remaining(),
			"score": self._score,
			"selected_verse": self._selected_verse,
			"last_closeness": self._last_closeness,
			"game_over": self._game_over,
		}

	def get_rounds_remaining(self) -> int | None:
		return self._rounds_remaining

	def get_lives_remaining(self) -> int | None:
		return self._lives_remaining

	def get_hints_remaining(self) -> int | None:
		mode: dict[str, Any] | None = self._selected_mode
		if mode is None:
			return None
		if mode["type"] == "endless":
			return self._endless_hints_remaining
		if mode["type"] == "finite":
			return max(mode.get("hints_per_round", 1) - self._hints_used_this_round, 0)
		return None

	def is_game_over(self) -> bool:
		return self._game_over

	@staticmethod
	def parse_answer(answer_text: str) -> dict[str, Any]:
		if not isinstance(answer_text, str):
			raise ValueError("Answer must be a string")

		match = re.match(r"^\s*(.+?)\s+(\d+)\s*:\s*(\d+)\s*$", answer_text)
		if match is None:
			raise ValueError("Answer format must be 'book_name chapter:verse'")

		book_name: str = match.group(1).strip()
		chapter: int = int(match.group(2))
		verse: int = int(match.group(3))
		if chapter < 1 or verse < 1:
			raise ValueError("Chapter and verse must be positive integers")

		return {"book_name": book_name, "chapter": chapter, "verse": verse}

	def _load_active_volumes(self) -> dict[str, Volume]:
		if not self._active_volumes_path.exists():
			raise FileNotFoundError(f"Active volumes file not found: {self._active_volumes_path}")

		with self._active_volumes_path.open("r", encoding="utf-8") as file:
			active_ids: list[Any] = json.load(file)

		if not isinstance(active_ids, list) or len(active_ids) == 0:
			raise ValueError("active_volumes must be a non-empty JSON array of volume ids")

		available_paths: dict[str, Path] = self._load_available_volume_paths()
		volumes: dict[str, Volume] = {}
		for volume_id in active_ids:
			if not isinstance(volume_id, str) or not volume_id.strip():
				raise ValueError("active_volumes contains an invalid volume id")

			normalized_id: str = volume_id.strip()
			if normalized_id not in available_paths:
				raise ValueError(f"No scripture data file found for volume id: {normalized_id}")

			volumes[normalized_id] = Volume(str(available_paths[normalized_id]))

		return volumes

	def _load_available_volume_paths(self) -> dict[str, Path]:
		if not self._scripture_data_dir.exists():
			raise FileNotFoundError(f"Scripture data directory not found: {self._scripture_data_dir}")

		volume_paths: dict[str, Path] = {}
		for json_path in sorted(self._scripture_data_dir.glob("*.json")):
			with json_path.open("r", encoding="utf-8") as file:
				volume_data: dict[str, Any] = json.load(file)

			volume_id = volume_data.get("id")
			if not isinstance(volume_id, str) or not volume_id.strip():
				raise ValueError(f"Volume file missing valid id: {json_path}")

			normalized_id: str = volume_id.strip()
			if normalized_id in volume_paths:
				raise ValueError(f"Duplicate volume id found in scripture data: {normalized_id}")

			volume_paths[normalized_id] = json_path

		return volume_paths

	def _load_game_settings(self) -> None:
		if not self._game_settings_path.exists():
			raise FileNotFoundError(f"Game settings file not found: {self._game_settings_path}")

		with self._game_settings_path.open("r", encoding="utf-8") as file:
			settings: dict[str, Any] = json.load(file)

		if not isinstance(settings, dict):
			raise ValueError("game_settings.json must contain a JSON object")

		modes = settings.get("modes")
		categories = settings.get("categories")
		scoring = settings.get("scoring")
		if not isinstance(modes, list) or len(modes) == 0:
			raise ValueError("game_settings.json must contain a non-empty 'modes' list")
		if not isinstance(categories, list) or len(categories) == 0:
			raise ValueError("game_settings.json must contain a non-empty 'categories' list")
		if not isinstance(scoring, dict):
			raise ValueError("game_settings.json must contain a 'scoring' object")

		self._modes_by_id = self._parse_modes(modes)
		self._categories_by_id = self._parse_categories(categories)
		self._scoring_config = self._parse_scoring(scoring)

	def _parse_scoring(self, scoring: dict[str, Any]) -> dict[str, Any]:
		max_round_points = scoring.get("max_round_points")
		finite_hint_multiplier = scoring.get("finite_hint_multiplier")
		tiers = scoring.get("tiers")

		if not isinstance(max_round_points, int) or max_round_points <= 0:
			raise ValueError("scoring.max_round_points must be a positive integer")
		if not isinstance(finite_hint_multiplier, (int, float)):
			raise ValueError("scoring.finite_hint_multiplier must be numeric")
		if not isinstance(tiers, dict):
			raise ValueError("scoring.tiers must be an object")

		parsed_tiers: dict[str, dict[str, int]] = {}
		for unit in ["verse", "chapter", "book"]:
			unit_tier = tiers.get(unit)
			if not isinstance(unit_tier, dict):
				raise ValueError(f"scoring.tiers.{unit} must be an object")
			unit_min = unit_tier.get("min")
			unit_max = unit_tier.get("max")
			if not isinstance(unit_min, int) or not isinstance(unit_max, int):
				raise ValueError(f"scoring.tiers.{unit} min/max must be integers")
			if unit_min < 0 or unit_max < 0 or unit_min > unit_max:
				raise ValueError(f"scoring.tiers.{unit} has invalid range")
			parsed_tiers[unit] = {"min": unit_min, "max": unit_max}

		if parsed_tiers["book"]["max"] >= parsed_tiers["chapter"]["min"]:
			raise ValueError("book tier must be strictly below chapter tier")
		if parsed_tiers["chapter"]["max"] >= parsed_tiers["verse"]["min"]:
			raise ValueError("chapter tier must be strictly below verse tier")
		if parsed_tiers["verse"]["max"] >= max_round_points:
			raise ValueError("verse tier max must be below max_round_points")

		return {
			"max_round_points": max_round_points,
			"finite_hint_multiplier": float(finite_hint_multiplier),
			"tiers": parsed_tiers,
		}

	def _parse_modes(self, modes: list[Any]) -> dict[str, dict[str, Any]]:
		parsed_modes: dict[str, dict[str, Any]] = {}
		for mode in modes:
			if not isinstance(mode, dict):
				raise ValueError("Each mode must be an object")

			mode_id = mode.get("id")
			mode_name = mode.get("name")
			mode_type = mode.get("type")
			if not isinstance(mode_id, str) or not mode_id.strip():
				raise ValueError("Each mode must have a non-empty string 'id'")
			if not isinstance(mode_name, str) or not mode_name.strip():
				raise ValueError(f"Mode '{mode_id}' must have a non-empty string 'name'")
			if mode_type not in {"endless", "finite"}:
				raise ValueError(f"Mode '{mode_id}' must have type 'endless' or 'finite'")
			if mode_id in parsed_modes:
				raise ValueError(f"Duplicate mode id found: {mode_id}")

			normalized_mode: dict[str, Any] = {
				"id": mode_id,
				"name": mode_name,
				"type": mode_type,
			}
			if mode_type == "endless":
				lives = mode.get("lives", 3)
				hints = mode.get("hints", 3)
				if not isinstance(lives, int) or lives <= 0:
					raise ValueError(f"Mode '{mode_id}' must have a positive integer 'lives'")
				if not isinstance(hints, int) or hints <= 0:
					raise ValueError(f"Mode '{mode_id}' must have a positive integer 'hints'")
				normalized_mode["lives"] = lives
				normalized_mode["hints"] = hints
			else:
				rounds = mode.get("rounds")
				hints_per_round = mode.get("hints_per_round", 1)
				if not isinstance(rounds, int) or rounds <= 0:
					raise ValueError(f"Mode '{mode_id}' must have a positive integer 'rounds'")
				if not isinstance(hints_per_round, int) or hints_per_round <= 0:
					raise ValueError(f"Mode '{mode_id}' must have a positive integer 'hints_per_round'")
				normalized_mode["rounds"] = rounds
				normalized_mode["hints_per_round"] = hints_per_round

			parsed_modes[mode_id] = normalized_mode

		return parsed_modes

	def _parse_categories(self, categories: list[Any]) -> dict[str, dict[str, Any]]:
		parsed_categories: dict[str, dict[str, Any]] = {}
		for category in categories:
			if not isinstance(category, dict):
				raise ValueError("Each category must be an object")

			category_id = category.get("id")
			category_name = category.get("name")
			volume_entries = category.get("volumes")
			if not isinstance(category_id, str) or not category_id.strip():
				raise ValueError("Each category must have a non-empty string 'id'")
			if not isinstance(category_name, str) or not category_name.strip():
				raise ValueError(f"Category '{category_id}' must have a non-empty string 'name'")
			if not isinstance(volume_entries, list) or len(volume_entries) == 0:
				raise ValueError(f"Category '{category_id}' must have a non-empty 'volumes' list")
			if category_id in parsed_categories:
				raise ValueError(f"Duplicate category id found: {category_id}")

			parsed_volume_entries: list[dict[str, Any]] = []
			seen_volume_ids: set[str] = set()
			for volume_entry in volume_entries:
				if not isinstance(volume_entry, dict):
					raise ValueError(f"Category '{category_id}' contains an invalid volume entry")

				volume_id = volume_entry.get("id")
				if not isinstance(volume_id, str) or not volume_id.strip():
					raise ValueError(f"Category '{category_id}' contains a volume entry with no id")

				normalized_volume_id = volume_id.strip()
				if normalized_volume_id in seen_volume_ids:
					raise ValueError(f"Category '{category_id}' contains duplicate volume id: {normalized_volume_id}")
				if normalized_volume_id not in self._volumes_by_id:
					raise ValueError(f"Category '{category_id}' references inactive volume: {normalized_volume_id}")
				seen_volume_ids.add(normalized_volume_id)

				book_ids = volume_entry.get("book_ids")
				normalized_book_ids: list[str] | None = None
				if book_ids is not None:
					if not isinstance(book_ids, list) or len(book_ids) == 0:
						raise ValueError(
							f"Category '{category_id}' volume '{normalized_volume_id}' must have a non-empty 'book_ids' list"
						)
					volume = self._volumes_by_id[normalized_volume_id]
					normalized_book_ids = []
					seen_books: set[str] = set()
					for book_id in book_ids:
						if not isinstance(book_id, str) or not book_id.strip():
							raise ValueError(
								f"Category '{category_id}' volume '{normalized_volume_id}' contains an invalid book id"
							)
						normalized_book_id = book_id.strip()
						if normalized_book_id in seen_books:
							raise ValueError(
								f"Category '{category_id}' volume '{normalized_volume_id}' contains duplicate book id: {normalized_book_id}"
							)
						volume.get_book_name(normalized_book_id)
						seen_books.add(normalized_book_id)
						normalized_book_ids.append(normalized_book_id)

				parsed_volume_entries.append(
					{
						"id": normalized_volume_id,
						"book_ids": normalized_book_ids,
					}
				)

			parsed_categories[category_id] = {
				"id": category_id,
				"name": category_name,
				"volumes": parsed_volume_entries,
			}

		return parsed_categories

	def _draw_target_from_selected_category(self) -> VerseRequest:
		category: dict[str, Any] = self._require_selected_category()
		options: list[tuple[Volume, list[str], int]] = []
		total_verses: int = 0
		for volume_entry in category["volumes"]:
			volume: Volume = self._get_volume(volume_entry["id"])
			book_ids: list[str] = volume_entry["book_ids"] if volume_entry["book_ids"] is not None else volume.get_all_book_ids()
			count: int = volume.get_total_verses_for_book_ids(book_ids)
			options.append((volume, book_ids, count))
			total_verses += count

		if total_verses <= 0:
			raise ValueError("Selected category has no verses available")

		random_verse_index: int = self._rng.randint(1, total_verses)
		for volume, book_ids, count in options:
			if random_verse_index > count:
				random_verse_index -= count
				continue
			selected: VerseRequest = volume.get_random_verse_from_book_ids(book_ids)
			self._selected_verse = selected
			self._selected_book_name = volume.get_book_name(selected.book)
			self._selected_volume_id = volume.volume_id
			return selected

		raise RuntimeError("Failed to resolve random verse for selected category")

	def _get_volume(self, volume_id: str) -> Volume:
		if volume_id not in self._volumes_by_id:
			raise ValueError(f"Volume is not active: {volume_id}")
		return self._volumes_by_id[volume_id]

	def _get_mode(self, mode_id: str) -> dict[str, Any]:
		if not isinstance(mode_id, str) or not mode_id.strip():
			raise ValueError("mode_id must be a non-empty string")
		normalized_mode_id = mode_id.strip()
		if normalized_mode_id not in self._modes_by_id:
			raise ValueError(f"Unknown mode: {normalized_mode_id}")
		return self._modes_by_id[normalized_mode_id]

	def _get_category(self, category_id: str) -> dict[str, Any]:
		if not isinstance(category_id, str) or not category_id.strip():
			raise ValueError("category_id must be a non-empty string")
		normalized_category_id = category_id.strip()
		if normalized_category_id not in self._categories_by_id:
			raise ValueError(f"Unknown category: {normalized_category_id}")
		return self._categories_by_id[normalized_category_id]

	def _require_selected_mode(self) -> dict[str, Any]:
		if self._selected_mode is None:
			raise ValueError("No mode selected")
		return self._selected_mode

	def _require_selected_category(self) -> dict[str, Any]:
		if self._selected_category is None:
			raise ValueError("No category selected")
		return self._selected_category

	def _reset_round_state(self, reset_score: bool = False) -> None:
		if reset_score:
			self._score = 0
		self._selected_verse = None
		self._selected_book_name = None
		self._selected_volume_id = None
		self._chapter_data = None
		self._last_closeness = None
		self._last_life_lost = False
		self._hints_used_this_round = 0

	def _extract_chapter_verses(self, chapter_data: dict | list) -> list[str]:
		if isinstance(chapter_data, list):
			return [str(verse_text) for verse_text in chapter_data]

		chapter = chapter_data.get("chapter")
		if not isinstance(chapter, dict):
			return []

		verse_entries = chapter.get("verses")
		if not isinstance(verse_entries, list):
			return []

		verses: list[str] = []
		for verse_entry in verse_entries:
			if isinstance(verse_entry, dict) and isinstance(verse_entry.get("text"), str):
				verses.append(verse_entry["text"])
		return verses

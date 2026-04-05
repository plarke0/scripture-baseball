import json
import re
from pathlib import Path

from shared.request_classes import VerseRequest
from shared.volume import Volume


class Game:
	def __init__(
		self,
		active_volumes_path: str = "active_volumes",
		scripture_data_dir: str = "shared/scripture_data"
	) -> None:
		self._scripture_data_dir: Path = Path(scripture_data_dir)
		self._active_volumes_path: Path = Path(active_volumes_path)
		self._volumes_by_id: dict[str, Volume] = self._load_active_volumes()

		self._round_number: int = 0
		self._selected_verse: VerseRequest | None = None
		self._selected_book_name: str | None = None
		self._chapter_data: dict | list | None = None
		self._last_closeness: dict | None = None

	def get_active_volume_ids(self) -> list[str]:
		return list(self._volumes_by_id.keys())

	def get_round_number(self) -> int:
		return self._round_number

	def select_random_target(self, volume_id: str, start_book: str, end_book: str) -> VerseRequest:
		volume: Volume = self._get_volume(volume_id)
		selected: VerseRequest = volume.get_random_verse_between_books(start_book, end_book)

		self._selected_verse = selected
		self._selected_book_name = volume.get_book_name(selected.book)
		self._chapter_data = None
		self._last_closeness = None
		self._round_number += 1

		return selected

	def set_chapter_data(self, chapter_data: dict | list) -> None:
		if not isinstance(chapter_data, (dict, list)):
			raise ValueError("Chapter data must be a dict or list")
		self._chapter_data = chapter_data

	def submit_answer(self, answer_text: str) -> dict:
		if self._selected_verse is None:
			raise ValueError("No active selected verse for this round")

		parsed_answer: dict = self.parse_answer(answer_text)
		closeness: dict = self.get_answer_closeness(
			self._selected_verse.volume,
			parsed_answer["book_name"],
			parsed_answer["chapter"],
			parsed_answer["verse"]
		)

		self._last_closeness = closeness

		return {
			"parsed_answer": parsed_answer,
			"closeness": closeness
		}

	def get_answer_closeness(
		self,
		volume_id: str,
		guess_book_name: str,
		guess_chapter: int,
		guess_verse: int
	) -> dict:
		if self._selected_verse is None or self._selected_book_name is None:
			raise ValueError("No active selected verse for this round")
		if self._selected_verse.volume != volume_id:
			raise ValueError("Selected verse is not in the requested volume")

		volume: Volume = self._get_volume(volume_id)
		volume.validate_verse_reference(guess_book_name, guess_chapter, guess_verse)

		target_book_name: str = self._selected_book_name
		target_chapter: int = self._selected_verse.chapter
		target_verse: int = self._selected_verse.verse

		if guess_book_name == target_book_name and guess_chapter == target_chapter and guess_verse == target_verse:
			return {
				"is_exact": True,
				"unit": "verse",
				"offset": 0,
				"absolute_offset": 0
			}

		if guess_book_name == target_book_name and guess_chapter == target_chapter:
			offset: int = target_verse - guess_verse
			return {
				"is_exact": False,
				"unit": "verse",
				"offset": offset,
				"absolute_offset": abs(offset)
			}

		if guess_book_name == target_book_name:
			offset = target_chapter - guess_chapter
			return {
				"is_exact": False,
				"unit": "chapter",
				"offset": offset,
				"absolute_offset": abs(offset)
			}

		target_book_index: int = volume.get_book_index(target_book_name)
		guess_book_index: int = volume.get_book_index(guess_book_name)
		offset = target_book_index - guess_book_index
		return {
			"is_exact": False,
			"unit": "book",
			"offset": offset,
			"absolute_offset": abs(offset)
		}

	def get_hint(self) -> list[str]:
		if self._selected_verse is None:
			raise ValueError("No active selected verse for this round")
		if self._chapter_data is None:
			raise ValueError("No chapter data set for this round")

		verses: list[str] = self._extract_chapter_verses(self._chapter_data)
		if len(verses) == 0:
			raise ValueError("Chapter data does not include verse text")

		target_index: int = self._selected_verse.verse - 1
		if target_index < 0 or target_index >= len(verses):
			raise ValueError("Selected verse is out of bounds for current chapter data")

		if len(verses) <= 3:
			return verses

		if target_index == 0:
			return verses[0:3]

		if target_index == len(verses) - 1:
			return verses[len(verses) - 3:len(verses)]

		return verses[target_index - 1:target_index + 2]

	def get_round_state(self) -> dict:
		return {
			"round_number": self._round_number,
			"selected_verse": self._selected_verse,
			"last_closeness": self._last_closeness
		}

	@staticmethod
	def parse_answer(answer_text: str) -> dict:
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

		return {
			"book_name": book_name,
			"chapter": chapter,
			"verse": verse
		}

	def _load_active_volumes(self) -> dict[str, Volume]:
		if not self._active_volumes_path.exists():
			raise FileNotFoundError(
				f"Active volumes file not found: {self._active_volumes_path}"
			)

		with self._active_volumes_path.open("r", encoding="utf-8") as file:
			active_ids: list = json.load(file)

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
				volume_data: dict = json.load(file)

			volume_id = volume_data.get("id")
			if not isinstance(volume_id, str) or not volume_id.strip():
				raise ValueError(f"Volume file missing valid id: {json_path}")

			normalized_id: str = volume_id.strip()
			if normalized_id in volume_paths:
				raise ValueError(f"Duplicate volume id found in scripture data: {normalized_id}")

			volume_paths[normalized_id] = json_path

		return volume_paths

	def _get_volume(self, volume_id: str) -> Volume:
		if volume_id not in self._volumes_by_id:
			raise ValueError(f"Volume is not active: {volume_id}")
		return self._volumes_by_id[volume_id]

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

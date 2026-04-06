import json
import random

from shared.request_classes import VerseRequest


class Volume:
	def __init__(self, json_file_path: str, rng: random.Random | None = None) -> None:
		self._volume_id: str = ""
		self._book_order: list[str] = []
		self._book_to_index: dict[str, int] = {}
		self._book_to_id: dict[str, str] = {}
		self._book_id_to_name: dict[str, str] = {}
		self._book_to_chapters: dict[str, list[int]] = {}
		self._book_to_total_verses: dict[str, int] = {}
		self._rng: random.Random = rng if rng is not None else random.Random()
		self._load_from_json(json_file_path)

	@property
	def volume_id(self) -> str:
		return self._volume_id

	def get_book_id(self, book_name: str) -> str:
		normalized_book: str = self._validate_book(book_name)
		return self._book_to_id[normalized_book]

	def get_book_name(self, book_id: str) -> str:
		if not isinstance(book_id, str) or not book_id.strip():
			raise ValueError("Book id must be a non-empty string")

		normalized_book_id: str = book_id.strip()
		if normalized_book_id not in self._book_id_to_name:
			raise ValueError(f"Unknown book id: {normalized_book_id}")

		return self._book_id_to_name[normalized_book_id]

	def get_book_index(self, book_name: str) -> int:
		normalized_book: str = self._validate_book(book_name)
		return self._book_to_index[normalized_book]

	def resolve_book_name(self, book_name: str) -> str:
		if not isinstance(book_name, str) or not book_name.strip():
			raise ValueError("Book must be a non-empty string")

		normalized_input: str = book_name.strip().lower()
		for canonical_book_name in self._book_order:
			if canonical_book_name.lower() == normalized_input:
				return canonical_book_name

		raise ValueError(f"Unknown book: {book_name.strip()}")

	def get_book_index_by_id(self, book_id: str) -> int:
		book_name: str = self.get_book_name(book_id)
		return self._book_to_index[book_name]

	def get_all_book_ids(self) -> list[str]:
		return [self._book_to_id[book_name] for book_name in self._book_order]

	def get_total_verses_for_book_ids(self, book_ids: list[str]) -> int:
		book_names: list[str] = self._normalize_book_ids(book_ids)
		total_verses: int = 0
		for book_name in book_names:
			total_verses += self._book_to_total_verses[book_name]
		return total_verses

	def get_random_verse_from_book_ids(self, book_ids: list[str]) -> VerseRequest:
		book_names: list[str] = self._normalize_book_ids(book_ids)
		total_verses: int = self.get_total_verses_for_book_ids(book_ids)

		random_verse_index: int = self._rng.randint(1, total_verses)
		for book_name in self._book_order:
			if book_name not in book_names:
				continue

			book_total_verses: int = self._book_to_total_verses[book_name]
			if random_verse_index > book_total_verses:
				random_verse_index -= book_total_verses
				continue

			chapters: list[int] = self._book_to_chapters[book_name]
			for chapter_number, chapter_verse_count in enumerate(chapters, start=1):
				if random_verse_index > chapter_verse_count:
					random_verse_index -= chapter_verse_count
					continue

				return VerseRequest(
					self._volume_id,
					self._book_to_id[book_name],
					chapter_number,
					random_verse_index
				)

		raise RuntimeError("Failed to resolve random verse in requested book subset")

	def validate_verse_reference(self, book_name: str, chapter: int, verse: int) -> None:
		chapter_verse_count: int = self.get_chapter_verse_count(book_name, chapter)
		if not isinstance(verse, int):
			raise ValueError("Verse must be an integer")
		if verse < 1 or verse > chapter_verse_count:
			raise ValueError(
				f"Invalid verse {verse} for {book_name} chapter {chapter}"
			)

	def get_chapter_verse_count(self, book: str, chapter: int) -> int:
		normalized_book: str = self._validate_book(book)
		return self._validate_and_get_chapter_count(normalized_book, chapter)

	def get_verses_between(
		self,
		start_book: str,
		start_chapter: int,
		end_book: str,
		end_chapter: int
	) -> int:
		normalized_start_book: str = self._validate_book(start_book)
		normalized_end_book: str = self._validate_book(end_book)

		self._validate_and_get_chapter_count(normalized_start_book, start_chapter)
		self._validate_and_get_chapter_count(normalized_end_book, end_chapter)

		start_key: tuple[int, int] = self._chapter_reference_key(normalized_start_book, start_chapter)
		end_key: tuple[int, int] = self._chapter_reference_key(normalized_end_book, end_chapter)
		if start_key > end_key:
			raise ValueError("Start reference must be before or equal to end reference")

		verse_total: int = 0
		is_counting: bool = False
		for book_name in self._book_order:
			chapters: list[int] = self._book_to_chapters[book_name]

			if book_name == normalized_start_book:
				is_counting = True
				chapter_start: int = start_chapter
			elif is_counting:
				chapter_start = 1
			else:
				continue

			if book_name == normalized_end_book:
				chapter_end: int = end_chapter
			else:
				chapter_end = len(chapters)

			for chapter_number in range(chapter_start, chapter_end + 1):
				verse_total += chapters[chapter_number - 1]

			if book_name == normalized_end_book:
				break

		return verse_total

	def get_random_verse_between_books(self, start_book: str, end_book: str) -> VerseRequest:
		normalized_start_book: str = self._validate_book(start_book)
		normalized_end_book: str = self._validate_book(end_book)

		start_index: int = self._book_to_index[normalized_start_book]
		end_index: int = self._book_to_index[normalized_end_book]
		if start_index > end_index:
			raise ValueError("Start book must be before or equal to end book")

		total_verses: int = 0
		for book_name in self._book_order[start_index:end_index + 1]:
			total_verses += self._book_to_total_verses[book_name]

		random_verse_index: int = self._rng.randint(1, total_verses)
		for book_name in self._book_order[start_index:end_index + 1]:
			book_total_verses: int = self._book_to_total_verses[book_name]
			if random_verse_index > book_total_verses:
				random_verse_index -= book_total_verses
				continue

			chapters: list[int] = self._book_to_chapters[book_name]
			for chapter_number, chapter_verse_count in enumerate(chapters, start=1):
				if random_verse_index > chapter_verse_count:
					random_verse_index -= chapter_verse_count
					continue

				return VerseRequest(
					self._volume_id,
					self._book_to_id[book_name],
					chapter_number,
					random_verse_index
				)

		raise RuntimeError("Failed to resolve random verse in requested range")

	def _load_from_json(self, file_path: str) -> None:
		with open(file_path, "r", encoding="utf-8") as file:
			data: dict = json.load(file)

		volume_id = data.get("id")
		if not isinstance(volume_id, str) or not volume_id.strip():
			raise ValueError("Volume JSON must contain a non-empty string 'id'")
		self._volume_id = volume_id.strip()

		books = data.get("books")
		if not isinstance(books, list) or len(books) == 0:
			raise ValueError("Volume JSON must contain a non-empty 'books' list")

		for book_entry in books:
			if not isinstance(book_entry, dict):
				raise ValueError("Each book entry must be an object")

			book_name = book_entry.get("name")
			book_id = book_entry.get("id")
			chapters = book_entry.get("chapters")

			if not isinstance(book_name, str) or not book_name.strip():
				raise ValueError("Each book must have a non-empty string 'name'")

			if not isinstance(book_id, str) or not book_id.strip():
				raise ValueError(f"Book '{book_name}' must have a non-empty string 'id'")

			if not isinstance(chapters, list) or len(chapters) == 0:
				raise ValueError(f"Book '{book_name}' must have a non-empty 'chapters' list")

			if book_name in self._book_to_chapters:
				raise ValueError(f"Duplicate book name found: {book_name}")

			if book_id in self._book_to_id.values():
				raise ValueError(f"Duplicate book id found: {book_id}")

			validated_chapters: list[int] = []
			for verse_count in chapters:
				if not isinstance(verse_count, int) or verse_count <= 0:
					raise ValueError(
						f"Book '{book_name}' has an invalid chapter verse count: {verse_count}"
					)
				validated_chapters.append(verse_count)

			self._book_order.append(book_name)
			self._book_to_index[book_name] = len(self._book_order) - 1
			self._book_to_id[book_name] = book_id
			self._book_id_to_name[book_id] = book_name
			self._book_to_chapters[book_name] = validated_chapters
			self._book_to_total_verses[book_name] = sum(validated_chapters)

	def _validate_book(self, book: str) -> str:
		if not isinstance(book, str) or not book.strip():
			raise ValueError("Book must be a non-empty string")

		normalized_book: str = book.strip()
		if normalized_book not in self._book_to_chapters:
			raise ValueError(f"Unknown book: {normalized_book}")

		return normalized_book

	def _validate_and_get_chapter_count(self, book: str, chapter: int) -> int:
		if not isinstance(chapter, int):
			raise ValueError("Chapter must be an integer")

		chapters: list[int] = self._book_to_chapters[book]
		if chapter < 1 or chapter > len(chapters):
			raise ValueError(f"Invalid chapter {chapter} for book '{book}'")

		return chapters[chapter - 1]

	def _chapter_reference_key(self, book: str, chapter: int) -> tuple[int, int]:
		return (self._book_to_index[book], chapter)

	def _normalize_book_ids(self, book_ids: list[str]) -> list[str]:
		if not isinstance(book_ids, list) or len(book_ids) == 0:
			raise ValueError("book_ids must be a non-empty list")

		normalized_book_names: list[str] = []
		seen_book_ids: set[str] = set()
		for book_id in book_ids:
			if not isinstance(book_id, str) or not book_id.strip():
				raise ValueError("Each book_id must be a non-empty string")

			normalized_book_id: str = book_id.strip()
			if normalized_book_id in seen_book_ids:
				raise ValueError(f"Duplicate book id found: {normalized_book_id}")

			seen_book_ids.add(normalized_book_id)
			normalized_book_names.append(self.get_book_name(normalized_book_id))

		ordered_book_names: list[str] = []
		for book_name in self._book_order:
			if book_name in normalized_book_names:
				ordered_book_names.append(book_name)

		if len(ordered_book_names) != len(normalized_book_names):
			raise ValueError("book_ids contain unknown values")

		return ordered_book_names

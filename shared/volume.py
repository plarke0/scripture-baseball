import json


class Volume:
	def __init__(self, json_file_path: str) -> None:
		self._book_order: list[str] = []
		self._book_to_chapters: dict[str, list[int]] = {}
		self._load_from_json(json_file_path)

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

	def _load_from_json(self, file_path: str) -> None:
		with open(file_path, "r", encoding="utf-8") as file:
			data: dict = json.load(file)

		books = data.get("books")
		if not isinstance(books, list) or len(books) == 0:
			raise ValueError("Volume JSON must contain a non-empty 'books' list")

		for book_entry in books:
			if not isinstance(book_entry, dict):
				raise ValueError("Each book entry must be an object")

			book_name = book_entry.get("name")
			chapters = book_entry.get("chapters")

			if not isinstance(book_name, str) or not book_name.strip():
				raise ValueError("Each book must have a non-empty string 'name'")

			if not isinstance(chapters, list) or len(chapters) == 0:
				raise ValueError(f"Book '{book_name}' must have a non-empty 'chapters' list")

			if book_name in self._book_to_chapters:
				raise ValueError(f"Duplicate book name found: {book_name}")

			validated_chapters: list[int] = []
			for verse_count in chapters:
				if not isinstance(verse_count, int) or verse_count <= 0:
					raise ValueError(
						f"Book '{book_name}' has an invalid chapter verse count: {verse_count}"
					)
				validated_chapters.append(verse_count)

			self._book_order.append(book_name)
			self._book_to_chapters[book_name] = validated_chapters

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
		return (self._book_order.index(book), chapter)

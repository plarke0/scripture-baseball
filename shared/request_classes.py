class VerseRequest:
    def __init__(self, volume: str, book: str, chapter: int, verse: int) -> None:
        self.volume: str = volume
        self.book: str = book
        self.chapter: int = chapter
        self.verse: int = verse
    
class RegisterRequest:
    ...
    
class LoginRequest:
    ...
    
class UpdateHighscoreRequest:
    ...
    
class TopScoresRequest:
    ...
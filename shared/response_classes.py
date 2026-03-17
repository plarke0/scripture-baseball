class VerseResponse:
    def __init__(self, chapter: list[str], verse: str) -> None:
        self.chapter: list[str] = chapter
        self.verse: str = verse
    
class RegisterResponse:
    ...
    
class LoginResponse:
    ...
    
class HighscoreResponse:
    ...
    
class TopScoresResponse:
    ...
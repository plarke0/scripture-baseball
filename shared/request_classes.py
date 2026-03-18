class VerseRequest:
    def __init__(self, volume: str, book: str, chapter: int, verse: int) -> None:
        self.volume: str = volume
        self.book: str = book
        self.chapter: int = chapter
        self.verse: int = verse
    
class RegisterRequest:
    def __init__(self, username: str, email: str, password: str) -> None:
        self.username: str = username
        self.email: str = email
        self.password: str = password
    
class LoginRequest:
    def __init__(self, username: str, password: str) -> None:
        self.username: str = username
        self.password: str = password
    
class UpdateHighscoreRequest:
    def __init__(self, score: int) -> None:
        self.score: int = score
    
class TopScoresRequest:
    def __init__(self, count: int) -> None:
        self.count: int = count
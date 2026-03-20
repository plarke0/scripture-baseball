from shared.data_classes import ScoreData

class VerseResponse:
    def __init__(self, chapter: list[str], verse: str) -> None:
        self.chapter: list[str] = chapter
        self.verse: str = verse
    
class RegisterResponse:
    def __init__(self, auth_token: str) -> None:
        self.auth_token: str = auth_token
    
class LoginResponse:
    def __init__(self, auth_token: str) -> None:
        self.auth_token: str = auth_token
    
class HighscoreResponse:
    def __init__(self, highscore: HighscoreData) -> None:
        self.highscore: HighscoreData = highscore
    
class TopScoresResponse:
    def __init__(self, top_scores: list[HighscoreData]) -> None:
        self.top_scores: list[HighscoreData] = top_scores
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
    def __init__(self, score: ScoreData) -> None:
        self.score: ScoreData = score
    
class TopScoresResponse:
    def __init__(self, top_scores: list[ScoreData]) -> None:
        self.top_scores: list[ScoreData] = top_scores
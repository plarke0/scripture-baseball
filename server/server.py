from shared.request_classes import VerseRequest, RegisterRequest, LoginRequest, UpdateHighscoreRequest, TopScoresRequest
from shared.response_classes import VerseResponse, RegisterResponse, LoginResponse, HighscoreResponse, TopScoresResponse

class Server:
    
    def __init__(self) -> None:
        ...
    
    def get_verse(self, auth_token: str, verse_request: VerseRequest) -> VerseResponse:
        ...
        
    def register_user(self, register_request: RegisterRequest) -> RegisterResponse:
        ...
        
    def login_user(self, login_request: LoginRequest) -> LoginResponse:
        ...
        
    def logout_user(self, auth_token: str) -> None:
        ...
        
    def get_highscore(self, auth_token: str) -> HighscoreResponse:
        ...
        
    def update_highscore(self, auth_token: str, update_highscore_request: UpdateHighscoreRequest) -> None:
        ...
        
    def get_top(self, auth_token: str, top_scores_request: TopScoresRequest) -> TopScoresResponse:
        ...
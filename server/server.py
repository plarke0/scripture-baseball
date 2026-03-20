from server.api_handlers import APIHandlers
from server.DAOs.auth_dao import AuthDAO
from server.DAOs.user_dao import UserDAO
from server.DAOs.score_dao import ScoreDAO
from shared.data_classes import AuthData, UserData, HighscoreData
from shared.request_classes import VerseRequest, RegisterRequest, LoginRequest, UpdateHighscoreRequest, TopScoresRequest
from shared.response_classes import VerseResponse, RegisterResponse, LoginResponse, HighscoreResponse, TopScoresResponse
from server.password_hashing import PasswordHasher
import uuid

class Server:
    
    def __init__(self) -> None:
        self.auth_dao = AuthDAO()
        self.user_dao = UserDAO()
        self.score_dao = ScoreDAO()
    
    def get_verse(self, auth_token: str, verse_request: VerseRequest) -> VerseResponse:
        self.check_auth(auth_token)
        
        volume: str = verse_request.volume
        book: str = verse_request.book
        chapter_number: int = verse_request.chapter
        verse_number: int = verse_request.verse
        
        chapter: list[str] = APIHandlers.get_chapter(volume, book, chapter_number)
        return VerseResponse(chapter, chapter[verse_number-1])
        
    def register_user(self, register_request: RegisterRequest) -> RegisterResponse:
        username: str = register_request.username
        email: str = register_request.email
        password: str = register_request.password
        hashed_password: str = PasswordHasher.hash_password(password)
        self.user_dao.insert_user(UserData(username, email, hashed_password))
        
        auth_data: AuthData = self.create_auth(username)
        
        return RegisterResponse(auth_data.auth_token)
        
    def login_user(self, login_request: LoginRequest) -> LoginResponse:
        username: str = login_request.username
        password: str = login_request.password
        user_data: UserData | None = self.user_dao.get_user(username)
        
        if user_data is None:
            raise ValueError("Username does not exist")
        
        if not PasswordHasher.check_password(password, user_data.password):
            raise ValueError("Incorrect password")
        
        auth_data: AuthData = self.create_auth(username)
        
        return LoginResponse(auth_data.auth_token)
        
    def logout_user(self, auth_token: str) -> None:
        self.auth_dao.delete_auth(auth_token)
        
    def get_highscore(self, auth_token: str) -> HighscoreResponse:
        ...
        
    def update_highscore(self, auth_token: str, update_highscore_request: UpdateHighscoreRequest) -> None:
        ...
        
    def get_top(self, auth_token: str, top_scores_request: TopScoresRequest) -> TopScoresResponse:
        ...
        
    def check_auth(self, auth_token: str) -> None:
        auth_data: AuthData | None = self.auth_dao.get_auth(auth_token)
        if auth_data is None:
            raise ValueError("Invalid auth token")
        
    def create_auth(self, username: str) -> AuthData:
        auth_token = str(uuid.uuid4())
        auth_data: AuthData = AuthData(username, auth_token)
        self.auth_dao.insert_auth(auth_data)
        return auth_data
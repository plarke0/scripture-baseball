class AuthData:
    def __init__(self, username: str, auth_token: str) -> None:
        self.username: str = username
        self.auth_token: str = auth_token
    
class UserData:
    def __init__(self, username: str, email: str, password: str) -> None:
        self.username: str = username
        self.email: str = email
        self.password: str = password
    
class ScoreData:
    def __init__(self, username: str, score: int) -> None:
        self.username: str = username
        self.score: int = score
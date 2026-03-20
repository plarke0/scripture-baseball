class AuthData:
    def __init__(self, username: str, auth_token: str) -> None:
        self.username: str = username
        self.auth_token: str = auth_token
    
class UserData:
    def __init__(self, username: str, email: str, password: str) -> None:
        self.username: str = username
        self.email: str = email
        self.password: str = password
    
class HighscoreData:
    def __init__(self, username: str, highscore: int) -> None:
        self.username: str = username
        self.highscore: int = highscore
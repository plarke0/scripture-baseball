from server.database_manager import DatabaseManager
from shared.data_classes import UserData

class UserDAO:
    
    def __init__(self) -> None:
        self.db_manager = DatabaseManager()
        
    def get_user(self, username: str) -> UserData:
        ...
        
    def insert_user(self, user_data: UserData) -> None:
        ...
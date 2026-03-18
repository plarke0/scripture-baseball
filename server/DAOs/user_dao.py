from server.database_manager import DatabaseManager
from shared.data_classes import UserData

class UserDAO:
    
    def __init__(self) -> None:
        self.db_manager = DatabaseManager()
        
    def get_user(self, username: str) -> UserData | None:
        sql = "SELECT username, email, password FROM users WHERE username = %s"
        val = (username, )
        
        user = self.db_manager.select_one(sql, val)
        if user is None:
            return
        
        return UserData(user[0], user[1], user[2])
        
    def insert_user(self, user_data: UserData) -> None:
        sql = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
        val = (user_data.username, user_data.email, user_data.password)
        self.db_manager.insert_with_commit(sql, val)
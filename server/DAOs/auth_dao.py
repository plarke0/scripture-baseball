from server.database_manager import DatabaseManager
from shared.data_classes import AuthData

class AuthDAO:
    
    def __init__(self) -> None:
        self.db_manager = DatabaseManager()
        
    def get_auth(self, auth_token: str) -> AuthData | None:
        sql = "SELECT user_id, auth_token FROM auths WHERE auth_token = %s"
        val = (auth_token, )
        
        auth = self.db_manager.select_one(sql, val)
        if auth is None:
            return None
        
        return AuthData(auth[0], auth[1])
        
    def insert_auth(self, auth_data: AuthData) -> None:
        sql = "SELECT user_id, auth_token FROM auths WHERE user_id = %s"
        val = (auth_data.username, )
        
        if not self.db_manager.select_one(sql, val):
            sql = "INSERT INTO auths (user_id, auth_token) VALUES (%s, %s)"
            val = (auth_data.username, auth_data.auth_token)
            self.db_manager.execute_with_commit(sql, val)
        else:
            sql = "UPDATE auths SET auth_token = %s WHERE user_id = %s"
            val = (auth_data.auth_token, auth_data.username)
            self.db_manager.execute_with_commit(sql, val)
        
    def delete_auth(self, auth_data: AuthData) -> None:
        sql = "DELETE FROM auths WHERE auth_token = %s"
        val = (auth_data.auth_token, )
        
        self.db_manager.execute_with_commit(sql, val)
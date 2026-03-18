from server.database_manager import DatabaseManager
from shared.data_classes import AuthData

class AuthDAO:
    
    def __init__(self) -> None:
        self.db_manager = DatabaseManager()
        
    def get_auth(self, auth_token: str) -> AuthData | None:
        cursor = self.db_manager.get_cursor()
        sql = "SELECT user_id, auth_token FROM auths WHERE auth_token = %s"
        values = (auth_token, )
        cursor.execute(sql, values)
        query_list: list[tuple] = cursor.fetchall() # type: ignore
        
        if len(query_list) == 0:
            return
        
        if len(query_list) > 1:
            raise ValueError("Found more than one entry for the given auth")
        
        return AuthData(query_list[0][0], query_list[0][1])
        
        
    def insert_auth(self, auth_data: AuthData) -> None:
        ...
        
    def delete_auth(self, auth_data: AuthData) -> None:
        ...
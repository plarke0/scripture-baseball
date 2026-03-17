from shared.data_classes import AuthData

class AuthDAO:
    
    def __init__(self) -> None:
        ...
        
    def get_auth(self, auth_token: str) -> AuthData:
        ...
        
    def insert_auth(self, auth_data: AuthData) -> None:
        ...
        
    def delete_auth(self, auth_data: AuthData) -> None:
        ...
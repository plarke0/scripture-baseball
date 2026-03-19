import bcrypt

class PasswordHasher:
    
    @staticmethod
    def hash_password(plain_text: str) -> str:
        byte_text: bytes = plain_text.encode()
        return str(bcrypt.hashpw(password=byte_text, salt=bcrypt.gensalt()))
    
    @staticmethod
    def check_password(plain_text: str, hash_text: str) -> bool:
        byte_plain_text: bytes = plain_text.encode()
        byte_hash_text: bytes = hash_text.encode()
        return bcrypt.checkpw(password=byte_plain_text, hashed_password=byte_hash_text)
import mysql.connector
import configparser

class DatabaseManager:
    
    tables: list[str] = [
        "users (username VARCHAR(255) PRIMARY KEY NOT NULL, email VARCHAR(255) NOT NULL, password VARCHAR(255) NOT NULL)",
        "auths (user_id VARCHAR(255), auth_token VARCHAR(255), FOREIGN KEY(user_id) REFERENCES users(username))",
        "highscores (user_id VARCHAR(255) NOT NULL, score INT, FOREIGN KEY(user_id) REFERENCES users(username))"
    ]
    
    def __init__(self):
        config = configparser.RawConfigParser()
        config.read('db.properties')
        
        host = config.get("DatabaseSection", "db.host")
        port = config.get("DatabaseSection", "db.port")
        user = config.get("DatabaseSection", "db.user")
        password = config.get("DatabaseSection", "db.password")
        database = config.get("DatabaseSection", "db.name")

        self.db = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
    def initialize_database(self):
        cursor = self.db.cursor()
        
        for table in self.tables:
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {table}")
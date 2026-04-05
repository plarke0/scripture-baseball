from server.database_manager import DatabaseManager
from shared.data_classes import HighscoreData

class ScoreDAO:
    
    def __init__(self) -> None:
        self.db_manager = DatabaseManager()
        
    def update_highscore(self, highscore_data: HighscoreData) -> None:
        sql = "SELECT user_id, category_id, score FROM highscores WHERE user_id = %s AND category_id = %s"
        val = (highscore_data.username, highscore_data.category_id)
        
        if self.db_manager.select_one(sql, val) is None:
            sql = "INSERT INTO highscores (user_id, category_id, score) VALUES (%s, %s, %s)"
            val = (highscore_data.username, highscore_data.category_id, highscore_data.highscore)
            self.db_manager.execute_with_commit(sql, val)
        else:
            sql = "UPDATE highscores SET score = %s WHERE user_id = %s AND category_id = %s"
            val = (highscore_data.highscore, highscore_data.username, highscore_data.category_id)
            self.db_manager.execute_with_commit(sql, val)
        
    def get_highscore(self, username: str, category_id: str) -> HighscoreData:
        sql = "SELECT user_id, category_id, score FROM highscores WHERE user_id = %s AND category_id = %s"
        val = (username, category_id)
        
        score = self.db_manager.select_one(sql, val)
        if score is None:
            return HighscoreData(username, category_id, 0)
        
        return HighscoreData(score[0], score[1], score[2])
        
    def get_top_scores(self, category_id: str, count: int) -> list[HighscoreData]:
        sql = "SELECT user_id, category_id, score FROM highscores WHERE category_id = %s ORDER BY score DESC LIMIT %s"
        val = (category_id, count)
        
        scores = self.db_manager.select_many(sql, val)
        return [HighscoreData(score[0], score[1], score[2]) for score in scores]
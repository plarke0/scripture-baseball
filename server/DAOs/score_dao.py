from shared.data_classes import ScoreData

class ScoreDAO:
    
    def __init__(self) -> None:
        self.db_manager = DatabaseManager()
        
    def update_highscore(self, highscore_data: HighscoreData) -> None:
        sql = "SELECT user_id, score FROM highscores WHERE user_id = %s"
        val = (highscore_data.username, )
        
        if not self.db_manager.select_one(sql, val):
            sql = "INSERT INTO highscores (user_id, score) VALUES (%s, %s)"
            val = (highscore_data.username, highscore_data.highscore)
            self.db_manager.execute_with_commit(sql, val)
        else:
            sql = "UPDATE highscores SET score = %s WHERE user_id = %s"
            val = (highscore_data.highscore, highscore_data.username)
            self.db_manager.execute_with_commit(sql, val)
        
    def get_highscore(self, username: str) -> HighscoreData:
        sql = "SELECT user_id, score FROM highscores WHERE user_id = %s"
        val = (username, )
        
        score = self.db_manager.select_one(sql, val)
        if score is None:
            return HighscoreData(username, 0)
        
        return HighscoreData(score[0], score[1])
        
    def get_top_scores(self, count: int) -> list[ScoreData]:
        ...
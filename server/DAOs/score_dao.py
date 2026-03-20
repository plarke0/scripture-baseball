from shared.data_classes import ScoreData

class ScoreDAO:
    
    def __init__(self) -> None:
        ...
        
    def get_highscore(self, username: str) -> HighscoreData:
        sql = "SELECT user_id, score FROM highscores WHERE user_id = %s"
        val = (username, )
        
        score = self.db_manager.select_one(sql, val)
        if score is None:
            return HighscoreData(username, 0)
        
        return HighscoreData(score[0], score[1])
        
    def get_top_scores(self, count: int) -> list[ScoreData]:
        ...
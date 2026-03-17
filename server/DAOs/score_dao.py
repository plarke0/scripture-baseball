from shared.data_classes import ScoreData

class AuthDAO:
    
    def __init__(self) -> None:
        ...
        
    def update_highscore(self, score_data: ScoreData) -> None:
        ...
        
    def get_auth(self, username: str) -> ScoreData:
        ...
        
    def get_top_scores(self, count: int) -> list[ScoreData]:
        ...
from __future__ import annotations

import json
from pathlib import Path

from server.server import Server
from shared.request_classes import (
    LoginRequest,
    RegisterRequest,
    TopScoresRequest,
    UpdateHighscoreRequest,
    VerseRequest,
)
from shared.response_classes import (
    HighscoreResponse,
    LoginResponse,
    RegisterResponse,
    TopScoresResponse,
    VerseResponse,
)


class FacadeServer:
    def __init__(self, game_settings_path: str = "game_settings.json") -> None:
        self._server: Server = Server()
        self._game_settings_path: Path = Path(game_settings_path)

    def load_game_settings(self) -> dict:
        with self._game_settings_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def register_user(self, username: str, email: str, password: str) -> RegisterResponse:
        return self._server.register_user(RegisterRequest(username, email, password))

    def login_user(self, username: str, password: str) -> LoginResponse:
        return self._server.login_user(LoginRequest(username, password))

    def logout_user(self, auth_token: str) -> None:
        self._server.logout_user(auth_token)

    def get_verse(self, auth_token: str, verse_request: VerseRequest) -> VerseResponse:
        return self._server.get_verse(auth_token, verse_request)

    def get_highscore(self, auth_token: str, category_id: str) -> HighscoreResponse:
        return self._server.get_highscore(auth_token, category_id)

    def update_highscore(self, auth_token: str, category_id: str, score: int) -> None:
        self._server.update_highscore(auth_token, category_id, UpdateHighscoreRequest(score))

    def get_top(self, auth_token: str, category_id: str, count: int) -> TopScoresResponse:
        return self._server.get_top(auth_token, category_id, TopScoresRequest(count))

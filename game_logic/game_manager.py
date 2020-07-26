from flask_sqlalchemy import SQLAlchemy

from Exceptions.internal_error import InternalError
from Exceptions.user_error import UserError
from db_models.game import Game
from game_logic.game_logic import GameLogic
from game_logic.gameparams import GameParams
import string
import random
from sqlalchemy.exc import IntegrityError

from session import SessionHelper, SessionKeys


def get_random_string(length):
    letters = string.ascii_uppercase + string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


class GameManager:
    def __init__(self, db: SQLAlchemy):
        self.db = db

    def CreateGame(self, params: GameParams) -> GameLogic:
        retries = 5
        while retries > 0:
            # TODO: Make sure this is cryptographically secure
            game_key = get_random_string(6)
            game = Game(uniqueCode=game_key, params=params.to_db(), roundsCompleted=0, isComplete=False)
            try:
                self.db.session.add(game)
                self.db.session.commit()
                return GameLogic(self.db, game)
            except IntegrityError as e:
                self.db.session.rollback()
                retries -= 1
                continue
        else:
            raise InternalError("Не удалось создать игру. Это странно.")

    def GetGame(self, game_key: str) -> GameLogic:
        game = Game.query.filter_by(uniqueCode=game_key).first()
        if game is None:
            # TODO: maybe remove the exception and make it Optional (everywhere)?
            raise UserError("К сожалению, такая игра не найдена. Проверьте уникальный код.")
        return GameLogic(self.db, game)

    def get_my_game(self):
        return self.GetGame(SessionHelper.get(SessionKeys.GAME_KEY))
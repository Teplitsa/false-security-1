from flask import Blueprint, redirect, url_for, render_template
from flask_socketio import SocketIO, emit, join_room
from dataclasses import dataclass

from Exceptions.user_error import UserError
from globals import db
from game_logic.game_manager import GameManager
from game_logic.player_manager import PlayerManager
from session import SessionHelper, SessionKeys

from utils.memoize import Memoize
from utils.response import Response
from globals import socketio

mod_game_wr = Blueprint('game_wr', __name__)


@dataclass
class WaitroomResponse:
    game_found: bool
    in_waitroom: bool = False
    game_name: str = None
    players: list = None
    can_start: bool = False
    is_admin: bool = False


def get_state():
    gm = GameManager(db)
    pm = PlayerManager(db)
    if not (SessionHelper.has(SessionKeys.PLAYER_ID) and SessionHelper.has(SessionKeys.GAME_KEY)):
        return WaitroomResponse(game_found=False)
    game = gm.get_my_game()
    if not game.is_waitroom():
        return WaitroomResponse(game_found=True, in_waitroom=False)
    return WaitroomResponse(
        game_found=True,
        in_waitroom=True,
        game_name=game.model.uniqueCode,
        players=[x.model.name for x in game.get_players()],
        can_start=game.can_start(pm.get_my_player()),
        is_admin=pm.get_my_player().model.isAdmin
    )


@socketio.on('waitroom')
def waitroom():
    try:
        result = get_state()
        join_room(result.game_name)
        emit('waitroom', Response.Ok(result).as_dicts())
        db.session.commit()
        db.session.remove()
    except Exception as e:
        emit('waitroom', Response.Error(str(e)).as_dicts())
        db.session.rollback()
        db.session.remove()


@Memoize
def get_game_manager():
    return GameManager(db)


@Memoize
def get_player_manager():
    return PlayerManager(db)


@mod_game_wr.route('/waitroom')
def wr():
    try:
        game = get_game_manager().get_my_game()
        player = get_player_manager().get_my_player()
    except UserError:
        return redirect(url_for('gameselect.index'))
    return render_template('waitroom.html')

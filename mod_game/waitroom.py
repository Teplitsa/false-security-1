from flask import Blueprint, redirect, url_for, render_template
from flask_socketio import SocketIO, emit, join_room
from dataclasses import dataclass

from Exceptions.user_error import UserError
from globals import db
from logic.game_manager import GameManager
from logic.player_manager import PlayerManager
from mod_gameselect.controller import ExitForm
from session import SessionHelper, SessionKeys
from utils.g_helper import set_current_player

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
    admin_player: str = None
    redirect_to: str = None
    game_link: str = None
    current_player: str = None



def get_state():
    gm = GameManager(db)
    pm = PlayerManager(db)
    if not (SessionHelper.has(SessionKeys.PLAYER_ID) and SessionHelper.has(SessionKeys.GAME_KEY)):
        return WaitroomResponse(game_found=False, redirect_to='/')
    game = gm.get_my_game()
    if not game.is_waitroom():
        return WaitroomResponse(game_found=True, in_waitroom=False, redirect_to='/game')
    return WaitroomResponse(
        game_found=True,
        in_waitroom=True,
        game_name=game.model.uniqueCode,
        current_player=pm.get_my_player().model.name,
        players=[{'name': x.model.name, 'is_admin': x.model.isAdmin, 'is_online': x.model.isOnline} for x in game.get_players()],
        can_start=game.can_start(pm.get_my_player()),
        game_link='?k=' + game.model.uniqueCode,
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
        emit('waitroom', Response.Error("Что-то сломалось.").as_dicts())
        db.session.rollback()
        db.session.remove()

@socketio.on('start')
def start_game():
    gm = get_game_manager()
    gm.get_my_game().start()

@Memoize
def get_game_manager():
    return GameManager(db)


@Memoize
def get_player_manager():
    return PlayerManager(db)


@mod_game_wr.route('/waitroom')
def wr():
    set_current_player()
    try:
        game = get_game_manager().get_my_game()
        player = get_player_manager().get_my_player()
    except UserError:
        return redirect(url_for('gameselect.index'))
    #TODO move ExitForm to different file
    return render_template('waitroom.html', form=ExitForm())

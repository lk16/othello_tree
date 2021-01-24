from typing import Dict

from flask import Blueprint, Response, jsonify, make_response

from othello.board import BLACK, MOVE_PASS, VALID_MOVE, WHITE, Board
from training.blueprints.api.bot import Bot

api = Blueprint("api", __name__)

API_BOT_DEPTH = 5


def board_details_children(board: Board) -> Dict[str, dict]:
    children: Dict[str, dict] = {}

    for index, field in enumerate(board.get_fields()):
        if field != VALID_MOVE:
            continue

        child = board.do_move(index)

        # make sure we pass if there are no moves
        if not child.has_moves():
            child = child.do_move(MOVE_PASS)

        children[str(index)] = {
            "id": child.to_id(),
        }

    return children


@api.route("/boards/<board_id>")
def board_details(board_id: str) -> Response:
    try:
        board = Board.from_id(board_id)
    except ValueError:
        return make_response("invalid board id", 400)

    children = board_details_children(board)

    result = {
        "id": board.to_id(),
        "children": children,
        "stats": {
            "discs": {
                "black": board.count(BLACK),
                "white": board.count(WHITE),
            },
            "moves": len(children),
        },
        "turn": {BLACK: "black", WHITE: "white"}[board.turn],
    }

    return jsonify(result)  # type: ignore


@api.route("/bot-moves/<board_id>")
def bot_moves_details(board_id: str) -> Response:
    try:
        board = Board.from_id(board_id)
    except ValueError:
        return make_response("invalid board id", 400)

    best_child = Bot(API_BOT_DEPTH).do_move(board)
    return board_details(best_child.to_id())

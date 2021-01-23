from typing import Dict

from flask import Blueprint, Response, jsonify, make_response

from othello.board import BLACK, MOVE_PASS, VALID_MOVE, WHITE, Board

api = Blueprint("api", __name__)


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


@api.route("/board/<board_id>")
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
    }

    return jsonify(result)  # type: ignore

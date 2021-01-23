from typing import Dict

from flask import Blueprint, Response, jsonify, make_response

from othello.board import BLACK, VALID_MOVE, WHITE, Board

api = Blueprint("api", __name__)


@api.route("/board/<board_id>")
def board_details(board_id: str) -> Response:
    try:
        board = Board.from_id(board_id)
    except ValueError:
        return make_response("invalid board id", 400)

    children: Dict[str, dict] = {}

    for index, field in enumerate(board.get_fields()):
        if field != VALID_MOVE:
            continue

        child = board.do_move(index)

        children[str(index)] = {
            "id": child.to_id(),
        }

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

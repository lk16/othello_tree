import json
from typing import Any, Dict, List

from flask import Blueprint, Response, jsonify, make_response

from othello.board import BLACK, MOVE_PASS, VALID_MOVE, WHITE, Board
from othello.openings_tree import OpeningsTree

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


def board_dict(board: Board) -> Dict[str, Any]:
    children = board_details_children(board)

    return {
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


@api.route("/boards/<board_id>")
def board_details(board_id: str) -> Response:
    try:
        board = Board.from_id(board_id)
    except ValueError:
        return make_response("invalid board id", 400)

    return jsonify(board_dict(board))  # type: ignore


@api.route("/openings")
def openings_list() -> Response:
    openings_tree = OpeningsTree.from_file("openings.json")
    openings = openings_tree.get_openings(WHITE) + openings_tree.get_openings(BLACK)
    return jsonify(openings)  # type: ignore

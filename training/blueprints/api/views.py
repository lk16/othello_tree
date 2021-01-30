import json
from typing import Any, Dict, List

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


def get_openings_recursive(
    tree: dict, openings: List[List[str]], prefix: List[str]
) -> None:

    if isinstance(tree, str):
        try:
            Board.field_to_index(tree)
        except ValueError:
            openings.append(prefix)
            return

        openings.append(prefix + [tree])
        return

    if isinstance(tree, dict):
        for move, subtree in tree.items():
            get_openings_recursive(subtree, openings, prefix + [move])
        return

    raise TypeError(f"unexpected type {type(tree)}")


def read_white_openings() -> List[dict]:
    tree = json.load(open("white.json", "r"))

    openings_list: List[List[str]] = []
    get_openings_recursive(tree, openings_list, [])

    response = []

    for opening in openings_list:
        moves: List[int] = [Board.field_to_index(field) for field in opening]

        # validate moves
        board = Board()
        for move in moves:
            board = board.do_move(move)

        if len(moves) % 2 != 0:
            moves = moves[:-1]

        opening_moves: List[dict] = []

        for i in range(len(moves) // 2):
            opening_moves.append({"move": moves[i * 2], "best_child": moves[i * 2 + 1]})

        response.append(
            {
                "start": Board().to_id(),
                "moves": opening_moves,
            }
        )

    return response


def read_black_openings() -> list:
    # TODO
    return []


@api.route("/openings")
def openings_list() -> Response:
    openings = read_white_openings() + read_black_openings()
    return jsonify(openings)  # type: ignore

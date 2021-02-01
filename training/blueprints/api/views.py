import json
from typing import Any, Dict, List

from flask import Blueprint, Response, jsonify, make_response

from othello.board import BLACK, MOVE_PASS, VALID_MOVE, WHITE, Board, opponent

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
            if tree == "transposition":
                return

            openings.append(prefix)
            return

        openings.append(prefix + [tree])
        return

    if isinstance(tree, dict):
        for move, subtree in tree.items():
            get_openings_recursive(subtree, openings, prefix + [move])
        return

    raise TypeError(f"unexpected type {type(tree)}")


def read_openings(color: int) -> list:
    filename = {WHITE: "white", BLACK: "black"}[color] + ".json"
    tree = json.load(open(filename, "r"))

    openings_list: List[List[str]] = []
    get_openings_recursive(tree, openings_list, [])

    response = []

    for opening in openings_list:
        moves: List[int] = [Board.field_to_index(field) for field in opening]

        opening_steps: List[dict] = []

        board = Board()

        if color == BLACK:
            board = board.do_move(moves[0])
            moves = moves[1:]

        for i in range(len(moves) // 2):
            move = moves[i * 2]
            best_child = moves[i * 2 + 1]

            assert opponent(color) == board.turn
            board = board.do_move(move)

            opening_steps.append(
                {"board": board.to_id(), "best_child": moves[i * 2 + 1]}
            )

            assert color == board.turn
            board = board.do_move(best_child)

        response.append(opening_steps)

    return response


@api.route("/openings")
def openings_list() -> Response:
    openings = read_openings(WHITE) + read_openings(BLACK)
    return jsonify(openings)  # type: ignore

import json
from typing import Dict, List, Optional, Union

from flask import Blueprint, Response, jsonify, make_response, request

from othello.board import Board

api = Blueprint("api", __name__)


def get_disc_offsets(args: str) -> List[int]:
    """
    Converts string with comma separated integers into list of integers.
    Ignores any errors. Also ignores any value less than 0 or larger than 63.
    """
    offsets = []
    for arg in args.split(","):
        try:
            offset = int(arg)
        except ValueError:
            continue
        if offset in range(64):
            offsets.append(offset)
    return offsets


@api.route("/move")
def do_move() -> Response:
    blacks = get_disc_offsets(request.args.get("black", ""))
    whites = get_disc_offsets(request.args.get("white", ""))

    turn = request.args.get("turn", "black")
    if turn not in ["0", "1"]:
        turn = "0"
    turn = int(turn)

    board = Board.from_indexes(blacks, whites, turn)

    move: Optional[str] = request.args.get("move")
    if not move:
        return make_response("missing move parameter", 400)

    try:
        move_index = int(move)
    except (ValueError, TypeError):
        return make_response("bad move formatting", 400)

    if board.get_moves() & (1 << move_index) == 0:
        return make_response("invalid move", 400)

    return jsonify(board.do_move(move_index).json())  # type: ignore


def get_openings(filename: str) -> List[List[str]]:
    try:
        tree = json.load(open(filename, "r"))
    except FileNotFoundError:
        return []

    openings: List[List[str]] = []

    def get_openings_rec(
        openings: List[List[str]], tree: Union[str, Dict[str, dict]], prefix: List[str]
    ) -> None:
        if isinstance(tree, dict):
            for move, subtree in tree.items():
                get_openings_rec(openings, subtree, prefix + [move])
            return

        if isinstance(tree, str):
            if tree != "transposition":
                openings += [prefix]
            return

        raise TypeError("unexpected", type(tree))

    get_openings_rec(openings, tree, [])

    return openings


@api.route("/openings")
def openings() -> Response:
    return jsonify(  # type: ignore
        {"white": get_openings("white.json"), "black": get_openings("black.json")}
    )

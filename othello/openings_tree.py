import json
from typing import Any, Dict, List, Set

from othello.board import MOVE_PASS, Board


class OpeningsTreeValidationError(Exception):
    pass


class OpeningsTree:
    def __init__(self) -> None:
        self.data: Dict[str, Dict[str, Any]] = {"openings": {}}

    @classmethod
    def from_file(cls, filename: str) -> "OpeningsTree":
        openings_tree = OpeningsTree()
        read_data = json.load(open(filename, "r"))
        openings_tree.data.update(read_data)
        return openings_tree

    def save(self, filename: str) -> None:
        self.validate()
        json.dump(self.data, open(filename, "w"), indent=4)

    def validate(self) -> None:
        for board_id, board_data in self.data["openings"].items():
            try:
                board = Board.from_id(board_id)
            except ValueError as e:
                raise OpeningsTreeValidationError(
                    f"board {board_id}: invalid ID"
                ) from e

            child_id = board_data["best_child"]

            try:
                Board.from_id(child_id)
            except ValueError as e:
                raise OpeningsTreeValidationError(
                    f"board {board_id}: invalid best_child ID"
                ) from e

            if child_id not in board.get_normalized_children_ids():
                raise OpeningsTreeValidationError(
                    f"board {board_id}: best_child is not a valid child"
                )

    def add_opening(self, color: int, fields: List[str]) -> None:
        board = Board()

        for field in fields:
            index = Board.field_to_index(field)

            if index == MOVE_PASS:
                raise ValueError("passing is not allowed in openings")

            board_id = board.get_normalized_id()

            try:
                child = board.do_move(index)
            except ValueError:
                raise ValueError(f"invalid move {field}")

            child_id = child.get_normalized_id()

            # only save boards for "color" in openings file
            if board.turn == color:
                self.add_opening_move(board_id, child_id)
            board = child

    def add_opening_move(self, board_id: str, child_id: str) -> None:
        self.data["openings"][board_id] = {"best_child": child_id}

    def root(self) -> dict:
        board_id = Board().get_normalized_id()
        return self.data["openings"][board_id]  # type: ignore

    def children(self, board_id: str) -> Set[str]:
        board = Board.from_id(board_id)
        return set(self.data["openings"].keys()) & board.get_normalized_children_ids()

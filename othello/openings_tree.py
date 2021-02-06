import json
from typing import Any, Dict, List

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
        openings_tree._validate()
        return openings_tree

    def save(self, filename: str) -> None:
        self._validate()
        json.dump(self.data, open(filename, "w"), indent=4)

    def _validate(self) -> None:
        for color in ["white", "black"]:
            self._validate_tree(color)
        self._validate_items()
        self._validate_no_unreachable()

    def _validate_items(self) -> None:
        for board_id, info in self.data["openings"].items():
            try:
                board = Board.from_id(board_id)
            except ValueError:
                raise OpeningsTreeValidationError(
                    f"board_id {board_id}: invalid board_id"
                )

            # TODO add Board.is_normalized()
            _, rotation = board.normalized()
            if rotation != 0:
                raise OpeningsTreeValidationError(
                    f"board_id {board_id}: un-normalized board_id"
                )

            if "best_child" in info:
                move = info["best_child"]

                _ = move
                # TODO check that best_child is a normalized child of board

    def _validate_tree(self, color: str) -> None:
        # TODO
        pass

    def _validate_subtree(self, color: str) -> None:
        # TODO
        pass

    def _validate_no_unreachable(self) -> None:
        # TODO
        pass

    def add_opening_move(self, board_id: str, best_child_id: str) -> None:
        if board_id not in self.data["openings"]:
            self.data["openings"][board_id] = {}

        existing_best_child_id = self.data["openings"][board_id].get("best_child")

        if existing_best_child_id not in [best_child_id, None]:
            raise ValueError("Inconsistent with existent openings")

        self.data["openings"][board_id].update({"best_child": best_child_id})

    def add_opening(self, color: int, fields: List[str]) -> None:
        board = Board()

        for field in fields:
            index = Board.field_to_index(field)

            if index == MOVE_PASS:
                raise ValueError("passing is not allowed in openings")

            board_id = board.normalized()[0].to_id()

            try:
                child = board.do_move(index)
            except ValueError:
                raise ValueError(f"invalid move {field}")

            best_child_id = child.normalized()[0].to_id()

            # only save boards for "color" in openings file
            if board.turn == color:
                self.add_opening_move(board_id, best_child_id)

            board = child

    def root(self) -> dict:
        board_id = Board().normalized()[0].to_id()
        return self.data["openings"][board_id]  # type: ignore

    def children(self, board_id: str) -> List[Any]:
        board = Board.from_id(board_id)

        children = []
        for child in board.get_normalized_children():
            child_id = child.to_id()
            if child_id in self.data["openings"]:
                children.append(child_id)

        return children

import json
from typing import Any, Dict, List, Set

from othello.board import BLACK, MOVE_PASS, WHITE, Board


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
        try:
            self.validate()
        except OpeningsTreeValidationError as e:
            print(f"VALIDATION FAILED: {e}")
        json.dump(self.data, open(filename, "w"), indent=4)

    def validate(self) -> None:
        for color in [WHITE, BLACK]:
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

            if not board.is_normalized():
                raise OpeningsTreeValidationError(
                    f"board_id {board_id}: un-normalized board_id"
                )

            if "best_child" in info:
                best_child = info["best_child"]

                if best_child not in board.get_normalized_children():
                    raise OpeningsTreeValidationError(
                        f"board_id {board_id}: invalid best_child {best_child}"
                    )

    def _validate_tree(self, color: int) -> None:
        board_id = Board().normalized()[0].to_id()
        self._validate_subtree(color, board_id)

    def _validate_subtree(self, color: int, board_id: str) -> None:
        board = Board.from_id(board_id)

        if board.turn == color:
            if board_id not in self.data["openings"]:
                raise OpeningsTreeValidationError(f"board_id {board_id}: missing")

            if "best_child" not in self.data["openings"][board_id]:
                raise OpeningsTreeValidationError(
                    f"board_id {board_id}: best_child value not found"
                )

            best_child_id = self.data["openings"][board_id]["best_child"]
            return self._validate_subtree(color, best_child_id)

        child_ids: Set[str] = board.get_normalized_children_ids()

        missing_child_ids: Set[str] = child_ids - set(self.data["openings"].keys())

        if len(missing_child_ids) not in [0, len(child_ids)]:
            raise OpeningsTreeValidationError(
                f"board_id {board_id}: missing children:\n"
                + "\n".join(sorted(missing_child_ids))
            )

        for child_id in child_ids:
            self._validate_subtree(color, child_id)

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

    def children(self, board_id: str) -> Set[str]:
        board = Board.from_id(board_id)
        return set(self.data["openings"].keys()) & board.get_normalized_children_ids()

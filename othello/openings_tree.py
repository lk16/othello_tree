import json
from typing import Any, Dict, Optional, Set

from othello.board import Board, opponent
from othello.game import Game


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

    def lookup(self, board: Board) -> Optional[Board]:
        board_id = board.get_normalized_id()
        openings = self.data["openings"]

        if board_id not in openings:
            return None

        return Board.from_id(openings[board_id]["best_child"])

    def add_opening_move(self, board_id: str, child_id: str) -> None:
        self.data["openings"][board_id] = {"best_child": child_id}

    def root(self) -> dict:
        board_id = Board().get_normalized_id()
        return self.data["openings"][board_id]  # type: ignore

    def children(self, board_id: str) -> Set[str]:
        board = Board.from_id(board_id)
        return set(self.data["openings"].keys()) & board.get_normalized_children_ids()

    def check(self, game: Game, player_name: str) -> None:
        if game.is_xot():
            raise ValueError("we don't check xot games")

        player_color = game.get_color(player_name)

        for index in range(len(game.boards) - 1):
            board = game.boards[index]
            child = game.boards[index + 1]

            if board.turn != player_color:
                continue

            if child.turn != opponent(player_color):
                print(f"move {index+1}: we don't check beyond passed turns")
                return

            best_child = self.lookup(board)

            if not best_child:
                print(f"move {index+1}: board not found in openings tree")
                return

            child_normalized, rotation = child.normalized()

            if child_normalized != best_child:
                print(f"move {index+1}: incorrect move")
                print()

                print("Board:")
                board.show()
                print()

                print("Played move:")
                child.show()
                print()

                print("Correct move:")
                best_child.denormalized(rotation).show()
                return

            print(f"move {index+1}: correct")

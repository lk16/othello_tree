import json
from typing import Any, Dict, Optional, Set

from othello.board import Board, opponent
from othello.game import Game


class OpeningsTreeValidationError(Exception):
    pass


class OpeningsTree:
    def __init__(self) -> None:
        self.data: Dict[str, Dict[str, Any]] = {"openings": {}}
        self.filename: Optional[str] = None

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

    def upsert(self, board: Board, best_child: Board) -> None:
        board_id = board.get_normalized_id()
        best_child_id = best_child.get_normalized_id()
        self.data["openings"][board_id] = {"best_child": best_child_id}

    def root(self) -> dict:
        board_id = Board().get_normalized_id()
        return self.data["openings"][board_id]  # type: ignore

    def children(self, board_id: str) -> Set[str]:
        board = Board.from_id(board_id)
        return set(self.data["openings"].keys()) & board.get_normalized_children_ids()

    def check(self, game: Game, player_name: str) -> None:

        if game.is_xot():
            print("we don't check xot games")
            return

        player_color = game.get_color(player_name)

        for move_offset in range(len(game.boards) - 1):
            board = game.boards[move_offset]
            child = game.boards[move_offset + 1]

            if board.turn != player_color:
                continue

            if child.turn != opponent(player_color):
                print(f"move {move_offset+1}: we don't check beyond passed turns")
                return

            best_child = self.lookup(board)

            if not best_child:
                print(f"move {move_offset+1}: not found")
                best_child = self.add_board_interactive(board, game, move_offset)

            child_normalized = child.normalized()[0]

            if child_normalized != best_child:
                print(f"move {move_offset+1}: wrong")
                print()

                print("Board:")
                board.show()
                print()

                print("Played move:")
                child.show()
                print()

                print("Correct move:")
                board.denormalize_child(best_child).show()
                return

            print(f"move {move_offset+1}: correct")

    def add_board_interactive(
        self, board: Board, game: Game, move_offset: int
    ) -> Board:
        board.show()
        print()

        move_sequence = " ".join(game.moves[:move_offset])
        print(f"Replay: {move_sequence}")

        move_fields = board.get_move_fields()

        print("Enter correct move:")
        while True:
            field = input("> ")

            if field in move_fields:
                break

        best_move = Board.field_to_index(field)
        best_child = board.do_move(best_move).normalized()[0]
        board_normalized = board.normalized()[0]
        self.upsert(board_normalized, best_child)
        return best_child

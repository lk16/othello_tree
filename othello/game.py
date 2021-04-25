from copy import copy
from typing import Dict, List

from othello.board import BLACK, WHITE, Board


class Game:
    def __init__(self) -> None:
        self.boards: List[Board] = []
        self.metadata: Dict[str, str] = {}

    @classmethod
    def from_pgn(cls, filename: str) -> "Game":
        with open(filename, "r") as file:
            contents = file.read()

        game = Game()

        lines = contents.split("\n")
        for offset, line in enumerate(lines):
            if not line.startswith("["):
                break

            split_line = line.split(" ")
            key = split_line[0][1:]
            value = split_line[1][1:-2]
            game.metadata[key] = value

        board = Board()
        game.boards.append(copy(board))

        for line in lines[offset:]:

            if line == "":
                continue

            for word in line.split(" "):
                if word[0].isdigit():
                    continue

                board = board.do_move(board.field_to_index(word))
                game.boards.append(copy(board))

        return game

    def get_color(self, player_name: str) -> int:
        if self.metadata["Black"] == player_name:
            return BLACK
        if self.metadata["White"] == player_name:
            return WHITE
        raise ValueError(f"Player {player_name} is not playing this game")

    def is_xot(self) -> bool:
        return self.metadata.get("Variant", "") == "xot"

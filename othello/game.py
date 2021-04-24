from copy import copy
from typing import Dict, List

from othello.board import Board


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

    def normalize(self) -> None:
        for index, board in enumerate(self.boards):
            self.boards[index] = board.normalized()[0]

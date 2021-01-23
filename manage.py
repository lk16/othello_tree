#!/usr/bin/env python

import json
import os
import re
from dataclasses import dataclass
from typing import List

import click
import requests
from bs4 import BeautifulSoup
from graphviz import Digraph
from PIL import Image, ImageDraw

BLACK = 0
WHITE = 1

MOVE_PASS = -1


@dataclass
class Board:
    me: int
    opp: int
    turn: int

    def __init__(self):
        self.me = 1 << 28 | 1 << 35
        self.opp = 1 << 27 | 1 << 36
        self.turn = BLACK

    def black(self) -> int:
        if self.turn == BLACK:
            return self.me
        return self.opp

    def white(self) -> int:
        if self.turn == WHITE:
            return self.me
        return self.opp

    def get_image_file_name(self):
        return "jpg/{0:0{1}x}{2:0{3}x}.jpg".format(
            self.black(),
            16,
            self.white(),
            16,
        )

    def write_image(self):
        filename = self.get_image_file_name()

        image_size = 100
        cell_size = image_size / 8
        disc_radius = 0.42 * cell_size
        color_black = (0, 0, 0)
        color_white = (255, 255, 255)

        im = Image.new("RGB", (image_size, image_size), (0, 192, 0))
        draw = ImageDraw.Draw(im)

        for i in range(1, 8):
            draw.line(
                (cell_size * i, 0, cell_size * i, image_size), fill=color_black, width=1
            )
            draw.line(
                (0, cell_size * i, image_size, cell_size * i), fill=color_black, width=1
            )

        for b in range(64):
            bit = 1 << b
            circle_x = (cell_size / 2) + cell_size * (b % 8)
            circle_y = (cell_size / 2) + cell_size * (b // 8)

            circle_coords = (
                circle_x - disc_radius,
                circle_y - disc_radius,
                circle_x + disc_radius,
                circle_y + disc_radius,
            )

            if self.white() & bit:
                draw.ellipse(circle_coords, fill=color_white, outline=color_white)

            if self.black() & bit:
                draw.ellipse(circle_coords, fill=color_black, outline=color_black)

        im.save(filename, quality=100)
        return filename

    @classmethod
    def field_to_index(cls, field: str) -> int:
        if len(field) != 2:
            raise ValueError("field too long")
        if field == "--":
            return MOVE_PASS
        x = ord(field[0]) - ord("a")
        y = ord(field[1]) - ord("1")
        if x not in range(8) or y not in range(8):
            raise ValueError("invalid field: {}".format(field))
        return 8 * y + x

    @classmethod
    def index_to_field(cls, index: int) -> str:
        if index not in range(64):
            raise ValueError("field index out of bounds")
        field = ""
        field += "abcdefgh"[index % 8]
        field += "12345678"[index // 8]
        return field

    def show(self) -> str:
        moves = self.get_moves()
        print("+-a-b-c-d-e-f-g-h-+")
        for y in range(8):
            print("{} ".format(y + 1), end="")
            for x in range(8):
                mask = 1 << ((y * 8) + x)
                if self.black() & mask:
                    print("○ ", end="")
                elif self.white() & mask:
                    print("● ", end="")
                elif moves & mask:
                    print("· ", end="")
                else:
                    print("  ", end="")
            print("|")
        print("+-----------------+")

    def do_move(self, move: int) -> "Board":
        if move == MOVE_PASS:
            child = Board()
            child.opp = self.me
            child.me = self.opp
            child.turn = 1 - self.turn
            return child

        if (self.me | self.opp) & (1 << move):
            raise ValueError(
                "invalid move: {} ({})".format(move, Board.index_to_field(move))
            )

        flipped = 0
        for dx, dy in [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]:
            s = 1
            while True:
                curx = int(move % 8) + (dx * s)
                cury = int(move / 8) + (dy * s)
                if curx < 0 or curx >= 8 or cury < 0 or cury >= 8:
                    break

                cur = 8 * cury + curx
                if self.opp & (1 << cur):
                    s += 1
                else:
                    if (self.me & (1 << cur)) and (s >= 2):
                        for p in range(1, s):
                            f = move + (p * (8 * dy + dx))
                            flipped |= 1 << f
                    break

        child = Board()
        child.opp = self.me | flipped | (1 << move)
        child.me = self.opp & ~child.opp
        child.turn = 1 - self.turn
        return child

    def get_moves(self) -> int:
        mask = self.opp & 0x7E7E7E7E7E7E7E7E

        flipL = mask & (self.me << 1)
        flipL |= mask & (flipL << 1)
        maskL = mask & (mask << 1)
        flipL |= maskL & (flipL << (2 * 1))
        flipL |= maskL & (flipL << (2 * 1))
        flipR = mask & (self.me >> 1)
        flipR |= mask & (flipR >> 1)
        maskR = mask & (mask >> 1)
        flipR |= maskR & (flipR >> (2 * 1))
        flipR |= maskR & (flipR >> (2 * 1))
        movesSet = (flipL << 1) | (flipR >> 1)

        flipL = mask & (self.me << 7)
        flipL |= mask & (flipL << 7)
        maskL = mask & (mask << 7)
        flipL |= maskL & (flipL << (2 * 7))
        flipL |= maskL & (flipL << (2 * 7))
        flipR = mask & (self.me >> 7)
        flipR |= mask & (flipR >> 7)
        maskR = mask & (mask >> 7)
        flipR |= maskR & (flipR >> (2 * 7))
        flipR |= maskR & (flipR >> (2 * 7))
        movesSet |= (flipL << 7) | (flipR >> 7)

        flipL = mask & (self.me << 9)
        flipL |= mask & (flipL << 9)
        maskL = mask & (mask << 9)
        flipL |= maskL & (flipL << (2 * 9))
        flipL |= maskL & (flipL << (2 * 9))
        flipR = mask & (self.me >> 9)
        flipR |= mask & (flipR >> 9)
        maskR = mask & (mask >> 9)
        flipR |= maskR & (flipR >> (2 * 9))
        flipR |= maskR & (flipR >> (2 * 9))
        movesSet |= (flipL << 9) | (flipR >> 9)

        flipL = self.opp & (self.me << 8)
        flipL |= self.opp & (flipL << 8)
        maskL = self.opp & (self.opp << 8)
        flipL |= maskL & (flipL << (2 * 8))
        flipL |= maskL & (flipL << (2 * 8))
        flipR = self.opp & (self.me >> 8)
        flipR |= self.opp & (flipR >> 8)
        maskR = self.opp & (self.opp >> 8)
        flipR |= maskR & (flipR >> (2 * 8))
        flipR |= maskR & (flipR >> (2 * 8))
        movesSet |= (flipL << 8) | (flipR >> 8)

        return movesSet & ~(self.me | self.opp) & 0xFFFFFFFFFFFFFFFF

    def get_children(self) -> List["Board"]:
        children = []
        moves = self.get_moves()
        for i in range(64):
            if moves & (1 << i):
                children.append(self.do_move(i))
        return children

    def count(self, color: int) -> int:
        if color == WHITE:
            return bin(self.white()).count("1")
        elif color == BLACK:
            return bin(self.black()).count("1")
        raise ValueError("Invalid color {}".format(color))


def generate_tree(dot, board, node, move_sequence=""):
    board_name = board.get_image_file_name()
    board_name = board.write_image()
    dot.node(board_name, label="", shape="plaintext", image=board_name)

    if type(node) is str:

        if node == "transposition":
            return

        child_name = board_name + node
        dot.node(child_name, node)
        dot.edge(board_name, child_name)
        return

    for move, subtree in node.items():
        child = board.do_move(Board.field_to_index(move))
        child_name = child.write_image()
        dot.node(child_name, label="", shape="plaintext", image=child_name)
        dot.edge(board_name, child_name)

        move_sequence_prefix = move_sequence + " " + move
        try:
            generate_tree(dot, child, subtree, move_sequence + " " + move)
        except ValueError as e:
            print(f"at {move_sequence_prefix}: {e}")
            exit(1)


@click.group()
def cli():
    pass


@cli.command()
def update_tree():
    dot = Digraph(format="png")
    board = Board()

    with open("white.json", "r") as json_file:
        tree_root = json.load(json_file)

    generate_tree(dot, board, tree_root)
    dot.render("white", cleanup=True)


PGN_FOLDER = "./pgn"


@cli.command()
@click.argument("username", type=str)
def download_playok_games(username):
    response = requests.get(
        f"https://www.playok.com/en/stat.phtml?u={username}&g=rv&sk=2"
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    downloaded_files = 0

    for trs in soup.find_all("tr")[1:]:
        tds = trs.findChildren("td")
        date = tds[0].text.strip().split(" ")[0]
        link = tds[-1].find("a", recursive=True)["href"]

        game_id = re.search("[0-9]+", link).group(0)
        filename = os.path.join(PGN_FOLDER, date, game_id + ".pgn")

        os.makedirs(os.path.join(PGN_FOLDER, date), exist_ok=True)

        if os.path.exists(filename):
            continue

        game_response = requests.get(f"https://www.playok.com{link}")
        game_response.raise_for_status()

        with open(filename, "w") as game_file:
            game_file.write(game_response.text)

        downloaded_files += 1

    print(f"Downloaded {downloaded_files} files.")


if __name__ == "__main__":
    cli()

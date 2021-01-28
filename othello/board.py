import json
import random
from dataclasses import dataclass
from typing import List, Tuple

from PIL import Image, ImageDraw

from othello.bits import bits_rotate

BLACK = 0
WHITE = 1
EMPTY = 2
VALID_MOVE = 3

MOVE_PASS = -1


@dataclass
class Board:
    me: int
    opp: int
    turn: int

    def __init__(self) -> None:
        self.me = 1 << 28 | 1 << 35
        self.opp = 1 << 27 | 1 << 36
        self.turn = BLACK

    @classmethod
    def from_discs(cls, me: int, opp: int, turn: int) -> "Board":
        board = Board()
        board.me = me
        board.opp = opp
        board.turn = turn
        return board

    @classmethod
    def from_xot(cls) -> "Board":
        xot_list = json.load(open("training/xot.json", "r"))
        xot = random.choice(xot_list)

        me = int(xot["me"][2:], 16)
        opp = int(xot["opp"][2:], 16)
        return Board.from_discs(me, opp, BLACK)

    @classmethod
    def from_id(cls, id_str: str) -> "Board":
        if id_str == "initial":
            return Board()

        if id_str == "xot":
            return Board.from_xot()

        if len(id_str) != 33:
            raise ValueError("unexpected id length")

        try:
            blacks = int(id_str[1:17], 16)
            whites = int(id_str[17:33], 16)
        except ValueError as e:
            raise ValueError("unexpected base 16 char in discs") from e

        if id_str[0] == "B":
            return Board.from_discs(blacks, whites, BLACK)
        if id_str[0] == "W":
            return Board.from_discs(whites, blacks, WHITE)

        raise ValueError("unexpected turn value")

    def black(self) -> int:
        if self.turn == BLACK:
            return self.me
        return self.opp

    def white(self) -> int:
        if self.turn == WHITE:
            return self.me
        return self.opp

    def get_image_file_name(self) -> str:
        return "jpg/{:016x}{:016x}.jpg".format(
            self.black(),
            self.white(),
        )

    def get_fields(self) -> List[int]:
        moves = self.get_moves()
        fields: List[int] = []
        black = self.black()
        white = self.white()

        for index in range(64):
            mask = 1 << index

            if black & mask:
                fields.append(BLACK)
            elif white & mask:
                fields.append(WHITE)
            elif moves & mask:
                fields.append(VALID_MOVE)
            else:
                fields.append(EMPTY)

        return fields

    def to_id(self) -> str:
        turn = {BLACK: "B", WHITE: "W"}[self.turn]
        return f"{turn}{self.black():016x}{self.white():016x}"

    def write_image(self) -> str:
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
        x = ord(field[0].lower()) - ord("a")
        y = ord(field[1]) - ord("1")
        if x not in range(8) or y not in range(8):
            raise ValueError("invalid field: {}".format(field))
        return 8 * y + x

    @classmethod
    def index_to_field(cls, index: int) -> str:
        if index == MOVE_PASS:
            return "--"
        if index not in range(64):
            raise ValueError("field index out of bounds")
        field = "abcdefgh"[index % 8]
        field += "12345678"[index // 8]
        return field

    def show(self) -> None:
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

    def has_moves(self) -> bool:
        return self.get_moves() != 0

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

    def normalized(self) -> Tuple["Board", int]:

        normalized = Board.from_discs(self.me, self.opp, self.turn)
        rotation = 0

        for r in range(1, 8):
            me = bits_rotate(self.me, r)
            opp = bits_rotate(self.opp, r)

            if me < normalized.me or (me == normalized.me and opp < normalized.opp):
                normalized.me = me
                normalized.opp = opp
                rotation = r

        return normalized, rotation

    def denormalized(self, rotation: int) -> "Board":
        unrotation = {
            0: 0,
            1: 1,
            2: 2,
            3: 3,
            4: 4,
            5: 6,
            6: 5,
            7: 7,
        }[rotation]

        return Board.from_discs(
            bits_rotate(self.me, unrotation),
            bits_rotate(self.opp, unrotation),
            self.turn,
        )

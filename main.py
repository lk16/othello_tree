from graphviz import Digraph
import svgwrite
from dataclasses import dataclass
from typing import List

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
    def get_svg_file_name(self):
        return "{0:0{1}x}{2:0{3}x}.svg".format(self.black(), 16, self.white(), 16)

    def write_svg(self):
        filename = self.get_svg_file_name()
        dwg = svgwrite.Drawing(filename)

        image_size = 400
        cell_size = image_size / 8
        disc_radius = 0.42 *cell_size

        dwg.add(dwg.rect((0, 0), (image_size, image_size), fill='green'))

        for i in range(1, 8):
            dwg.add(svgwrite.shapes.Line(start=(cell_size*i, 0), end=(cell_size*i, image_size), stroke='black'))
            dwg.add(svgwrite.shapes.Line(start=(0, cell_size*i), end=(image_size, cell_size*i), stroke='black'))

        for b in range(64):
            bit = 1 << b
            circle_x = (cell_size/2) + cell_size*(b % 8)
            circle_y = (cell_size/2) + cell_size*(b // 8)
            if self.white() & bit:
                dwg.add(dwg.circle(center=(circle_x, circle_y), r=disc_radius, fill='white'))
            if self.black() & bit:
                dwg.add(dwg.circle(center=(circle_x, circle_y), r=disc_radius, fill='black'))
        dwg.save()

        return filename

    @classmethod
    def field_to_index(cls, field: str) -> int:
        if len(field) != 2:
            raise ValueError("field too long")
        if field == '--':
            return MOVE_PASS
        x = ord(field[0]) - ord('a')
        y = ord(field[1]) - ord('1')
        if x not in range(8) or y not in range(8):
            raise ValueError("invalid field: {}".format(field))
        return 8*y + x

    def show(self) -> str:
        moves = self.get_moves()
        print('+-a-b-c-d-e-f-g-h-+')
        for y in range(8):
            print('{} '.format(y+1), end='')
            for x in range(8):
                mask = 1 << ((y*8) + x)
                if self.black() & mask:
                    print('○ ', end='')
                elif self.white() & mask:
                    print('● ', end='')
                elif moves & mask:
                    print('· ', end='')
                else:
                    print('  ', end='')
            print('|')
        print('+-----------------+')

    def do_move(self, move: int) -> 'Board':
        if move == MOVE_PASS:
            child = Board()
            child.opp = self.me
            child.me = self.opp
            child.turn = 1 - self.turn
            return child

        if (self.me | self.opp) & (1 << move):
            raise ValueError('invalid move: {}'.format(move))

        flipped = 0
        for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            s = 1
            while True:
                curx = int(move % 8) + (dx * s)
                cury = int(move / 8) + (dy * s)
                if curx < 0 or curx >= 8 or cury < 0 or cury >= 8:
                    break

                cur = 8*cury + curx
                if self.opp & (1 << cur):
                    s += 1
                else:
                    if (self.me & (1 << cur)) and (s >= 2):
                        for p in range(1, s):
                            f = move + (p*(8*dy+dx))
                            flipped |= (1 << f)
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

    def get_children(self) -> List['Board']:
        children = []
        moves = self.get_moves()
        for i in range(64):
            if moves & (1 << i):
                children.append(self.do_move(i))
        return children

    def count(self, color: int) -> int:
        if color == WHITE:
            return bin(self.white()).count('1')
        elif color == BLACK:
            return bin(self.black()).count('1')
        raise ValueError('Invalid color {}'.format(color))



def main():

    Board().write_svg()

    return

    dot = Digraph(format='png')

    dot.node('a', shape='plaintext', image='foo.jpeg')
    dot.node('b', shape='plaintext', image='bar.jpeg')
    dot.edge('a', 'b')
    dot.render('graph')

if __name__ == '__main__':
    main()

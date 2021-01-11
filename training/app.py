from flask import Flask, jsonify, render_template, make_response, request
import json
from othello.board import Board, MOVE_PASS, BLACK
from typing import List

app = Flask(__name__)


def get_openings(filename):
    try:
        tree = json.load(open(filename, 'r'))
    except FileNotFoundError:
        return []

    openings = []

    def get_openings_rec(openings, tree, prefix):
        if isinstance(tree, dict):
            for move, subtree in tree.items():
                get_openings_rec(openings, subtree, prefix + [move])
            return

        if isinstance(tree, str):
            if tree != 'transposition':
                openings += [prefix]
            return

        raise TypeError('unexpected', type(tree))

    get_openings_rec(openings, tree, [])

    return openings


@app.route('/openings')
def openings():
    return jsonify({
        "white": get_openings("white.json"),
        "black": get_openings("black.json")
    })


@app.route('/')
def index():
    return render_template('index.html')

def get_disc_offsets(args: str) -> List[int]:
    """
    Converts string with comma separated integers into list of integers.
    Ignores any errors. Also ignores any value less than 0 or larger than 63.
    """
    offsets = []
    for arg in args.split(','):
        try:
            offset = int(arg)
        except ValueError:
            continue
        if offset in range(64):
            offsets.append(offset)
    return offsets


@app.route('/board')
def board_image():
    blacks = get_disc_offsets(request.args.get('black', ''))
    whites = get_disc_offsets(request.args.get('white', ''))
    wrongs = get_disc_offsets(request.args.get('wrong', ''))

    turn = request.args.get('turn', 'black')
    if turn not in ['0', '1']:
        turn = '0'
    turn = int(turn)

    image_size = 800
    cell_size = image_size / 8
    disc_radius = 0.38 * cell_size
    move_radius = 0.08 * cell_size
    cross_width = 0.3 * cell_size

    body = f"""<?xml version="1.0"?>
    <svg width="{image_size}" height="{image_size}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <rect x="0" y="0" width="{image_size}" height="{image_size}" style="fill:green; stroke-width:2; stroke:black" />
    """

    for i in range(1, 8):
        offset = int(cell_size*i)
        body += f'<line x1="{offset}" y1="0" x2="{offset}" y2="{image_size}" style="stroke:black; stroke-width:2" />\n'
        body += f'<line x1="0" y1="{offset}" x2="{image_size}" y2="{offset}" style="stroke:black; stroke-width:2" />\n'

    for (color, indexes) in [("black", blacks), ("white", whites)]:
        for index in indexes:
            circle_x = (cell_size/2) + cell_size*(index % 8)
            circle_y = (cell_size/2) + cell_size*(index // 8)
            body += f'<circle cx="{circle_x}" cy="{circle_y}" r="{disc_radius}" fill="{color}" />\n'

    for index in wrongs:
        cross_min_x = (cell_size/2) + cell_size*(index % 8) - (cross_width/2)
        cross_min_y = (cell_size/2) + cell_size*(index // 8) - (cross_width/2)
        cross_max_x = cross_min_x + cross_width
        cross_max_y = cross_min_y + cross_width

        body += f'<line x1="{cross_min_x}" y1="{cross_min_y}" x2="{cross_max_x}" y2="{cross_max_y}" style="stroke:red; stroke-width:7" />\n'
        body += f'<line x1="{cross_max_x}" y1="{cross_min_y}" x2="{cross_min_x}" y2="{cross_max_y}" style="stroke:red; stroke-width:7" />\n'

    board = Board.from_indexes(blacks, whites, turn)
    moves_bitset = board.get_moves()
    for index in range(64):
        if moves_bitset & (1 << index):
            circle_x = (cell_size/2) + cell_size*(index % 8)
            circle_y = (cell_size/2) + cell_size*(index // 8)
            body += f'<circle cx="{circle_x}" cy="{circle_y}" r="{move_radius}" fill="{turn}" />\n'

    body += """
    </svg>
    """

    response = make_response(body)
    response.content_type = 'image/svg+xml'
    return response


@app.route('/move')
def do_move():
    blacks = get_disc_offsets(request.args.get('black', ''))
    whites = get_disc_offsets(request.args.get('white', ''))

    turn = request.args.get('turn', 'black')
    if turn not in ['0', '1']:
        turn = '0'
    turn = int(turn)

    board = Board.from_indexes(blacks, whites, turn)

    move = request.args.get("move")
    try:
        move = int(move)
    except (ValueError, TypeError):
        return make_response("bad move formatting", 400)

    if board.get_moves() & (1 << move) == 0:
        return make_response("invalid move", 400)

    return jsonify(board.do_move(move).json())

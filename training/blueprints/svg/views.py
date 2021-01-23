from flask import Blueprint, Response, make_response

from othello.board import BLACK, EMPTY, VALID_MOVE, WHITE, Board

svg = Blueprint("svg", __name__)


@svg.route("/board/<board_id>")
def board_image(board_id: str) -> Response:
    try:
        board = Board.from_id(board_id)
    except ValueError:
        return make_response("Invalid board", 400)

    image_size = 800
    cell_size = image_size / 8
    disc_radius = 0.38 * cell_size
    move_radius = 0.08 * cell_size
    # cross_width = 0.3 * cell_size TODO

    body = f"""<?xml version="1.0"?>
    <svg width="{image_size}" height="{image_size}" xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink">
    <rect x="0" y="0" width="{image_size}" height="{image_size}"
    style="fill:green; stroke-width:2; stroke:black" />
    """

    for i in range(1, 8):
        offset = int(cell_size * i)
        body += f"""<line x1="{offset}" y1="0" x2="{offset}" y2="{image_size}"
        style="stroke:black; stroke-width:2" />\n"""
        body += f"""<line x1="0" y1="{offset}" x2="{image_size}" y2="{offset}"
        style="stroke:black; stroke-width:2" />\n"""

    for index, field in enumerate(board.get_fields()):
        circle_x = (cell_size / 2) + cell_size * (index % 8)
        circle_y = (cell_size / 2) + cell_size * (index // 8)

        move_color = {BLACK: "black", WHITE: "white"}[board.turn]

        if field == VALID_MOVE:
            body += f"""<circle cx="{circle_x}" cy="{circle_y}"
            r="{move_radius}" fill="{move_color}" />\n"""
            continue

        if field == EMPTY:
            continue

        fill_color = {BLACK: "black", WHITE: "white"}[field]

        body += f"""<circle cx="{circle_x}" cy="{circle_y}"
        r="{disc_radius}" fill="{fill_color}" />\n"""

    # TODO
    # for index in wrongs:
    #     cross_min_x = (cell_size / 2) + cell_size * (index % 8) - (cross_width / 2)
    #     cross_min_y = (cell_size / 2) + cell_size * (index // 8) - (cross_width / 2)
    #     cross_max_x = cross_min_x + cross_width
    #     cross_max_y = cross_min_y + cross_width
    #
    #     body += f"""<line x1="{cross_min_x}" y1="{cross_min_y}"
    #     x2="{cross_max_x}" y2="{cross_max_y}" style="stroke:red;
    #     stroke-width:7" />\n
    #     <line x1="{cross_max_x}" y1="{cross_min_y}"
    #     x2="{cross_min_x}" y2="{cross_max_y}" style="stroke:red;
    #     stroke-width:7" />\n"""

    body += "</svg>"

    response = make_response(body)
    response.content_type = "image/svg+xml"
    return response

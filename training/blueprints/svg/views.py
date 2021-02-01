from typing import Set

from flask import Blueprint, Response, make_response, request

from othello.board import BLACK, EMPTY, VALID_MOVE, WHITE, Board

svg = Blueprint("svg", __name__)


@svg.route("/boards/<board_id>")
def board_image(board_id: str) -> Response:
    try:
        board = Board.from_id(board_id)
    except ValueError:
        return make_response("Invalid board", 400)

    image_size = 800
    cell_size = image_size / 8
    disc_radius = 0.38 * cell_size
    move_radius = 0.08 * cell_size
    cross_width = 0.3 * cell_size

    body = f"""<?xml version="1.0"?>
    <svg width="{image_size}" height="{image_size}" xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink">
    <defs>
        <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color: rgb(120,120,120);stop-opacity:1" />
            <stop offset="100%" style="stop-color: black;stop-opacity:1" />
        </linearGradient>
        <linearGradient id="grad2" x1="15%" y1="15%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color: white;stop-opacity:1" />
            <stop offset="100%" style="stop-color:rgb(150,150,150);stop-opacity:1" />
        </linearGradient>
    </defs>
    <rect x="0" y="0" width="{image_size}" height="{image_size}"
    style="fill:green; stroke-width:2; stroke:black" />
    """

    for i in range(1, 8):
        offset = int(cell_size * i)
        body += f"""<line x1="{offset}" y1="0" x2="{offset}" y2="{image_size}"
        style="stroke:black; stroke-width:2" />\n"""
        body += f"""<line x1="0" y1="{offset}" x2="{image_size}" y2="{offset}"
        style="stroke:black; stroke-width:2" />\n"""

    mistakes = request.args.get("mistakes", "")
    print(mistakes)

    mistake_indexes: Set[int] = set()

    for index in mistakes.split(","):
        try:
            mistake_indexes.add(int(index))
        except ValueError:
            pass

    for index, field in enumerate(board.get_fields()):
        circle_x = (cell_size / 2) + cell_size * (index % 8)
        circle_y = (cell_size / 2) + cell_size * (index // 8)

        move_color = {BLACK: "black", WHITE: "white"}[board.turn]

        if field == VALID_MOVE:

            if index in mistake_indexes:
                cross_min_x = (
                    (cell_size / 2) + cell_size * (index % 8) - (cross_width / 2)
                )
                cross_min_y = (
                    (cell_size / 2) + cell_size * (index // 8) - (cross_width / 2)
                )
                cross_max_x = cross_min_x + cross_width
                cross_max_y = cross_min_y + cross_width

                body += f"""<line x1="{cross_min_x}" y1="{cross_min_y}"
                x2="{cross_max_x}" y2="{cross_max_y}" style="stroke:red;
                stroke-width:7" />\n
                <line x1="{cross_max_x}" y1="{cross_min_y}"
                x2="{cross_min_x}" y2="{cross_max_y}" style="stroke:red;
                stroke-width:7" />\n"""
                continue

            body += f"""<circle cx="{circle_x}" cy="{circle_y}"
            r="{move_radius}" fill="{move_color}" />\n"""
            continue

        if field == EMPTY:
            continue

        if field == BLACK:
            body += f"""
            <circle cx="{circle_x}" cy="{circle_y}" r="{disc_radius}"
            fill="url(#grad1)" />
            <circle cx="{circle_x}" cy="{circle_y}" r="{disc_radius}" stroke="#222222"
            stroke-width="8" fill="none" />
            """
            continue

        if field == WHITE:
            body += f"""
            <circle cx="{circle_x}" cy="{circle_y}" r="{disc_radius}"
            fill="url(#grad2)" />
            <circle cx="{circle_x}" cy="{circle_y}" r="{disc_radius}" stroke="#DDDDDD"
            stroke-width="8" fill="none" />
            """

    body += "</svg>"

    response = make_response(body)
    response.content_type = "image/svg+xml"

    if board_id == "xot":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    return response

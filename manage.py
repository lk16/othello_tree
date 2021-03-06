#!/usr/bin/env python

import glob
import json
import os
import re
from typing import Dict, Union

import click
import requests
from bs4 import BeautifulSoup
from graphviz import Digraph

from othello.board import Board
from othello.game import Game
from othello.openings_tree import OpeningsTree

PGN_FOLDER: str = "./pgn"


def generate_tree(
    dot: Digraph,
    board: Board,
    node: Union[str, Dict[str, Union[dict, str]]],
    move_sequence: str = "",
) -> None:
    board_name = board.get_image_file_name()
    board_name = board.write_image()
    dot.node(board_name, label="", shape="plaintext", image=board_name)

    if isinstance(node, str):

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
def cli() -> None:
    pass


@cli.command()
def update_tree_images() -> None:
    dot = Digraph(format="png")
    board = Board()

    with open("white.json", "r") as json_file:
        tree_root = json.load(json_file)

    generate_tree(dot, board, tree_root)
    dot.render("white", cleanup=True)

    dot = Digraph(format="png")
    board = Board()

    with open("black.json", "r") as json_file:
        tree_root = json.load(json_file)

    generate_tree(dot, board, tree_root)
    dot.render("black", cleanup=True)


@cli.command()
@click.argument("username", type=str)
def download_playok_games(username: str) -> None:
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

        match = re.search("[0-9]+", link)

        if not match:
            raise ValueError("regex didn't match")

        game_id = match.group(0)
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


@cli.command()
def runserver() -> None:
    from training.app import app

    app.run(host="0.0.0.0", port=5000, debug=True)


@cli.command()
@click.argument("player_name", type=str)
@click.argument("path", type=str)
def check_pgn(
    player_name: str,
    path: str,
) -> None:

    if os.path.isdir(path):
        filenames = sorted(list(glob.glob(path + "/**/*.pgn")), reverse=True)
    else:
        filenames = [path]

    openings_filename = "openings.json"
    openings_tree = OpeningsTree.from_file(openings_filename)

    for i, filename in enumerate(filenames):
        print(f"checking file {i+1}/{len(filenames)}: {filename}")
        game = Game.from_pgn(filename)

        openings_tree.check(game, player_name)
        openings_tree.save(openings_filename)


@cli.group()
def openings() -> None:
    pass


@openings.command()
@click.argument("board_id", type=str)
def show(board_id: str) -> None:
    board = Board.from_id(board_id)
    board.show()


if __name__ == "__main__":
    cli()

from flask import Flask, jsonify, render_template
import json

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

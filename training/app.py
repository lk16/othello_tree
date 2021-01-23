from flask import Flask, render_template

from training.blueprints.api.views import api
from training.blueprints.svg.views import svg

app = Flask(__name__)
app.register_blueprint(svg)
app.register_blueprint(api)


@app.route("/")
def index() -> str:
    return render_template("index.html")

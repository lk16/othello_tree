from flask import Flask, render_template
from training.blueprints.svg.views import svg
from training.blueprints.api.views import api

app = Flask(__name__)
app.register_blueprint(svg)
app.register_blueprint(api)


@app.route('/')
def index():
    return render_template('index.html')

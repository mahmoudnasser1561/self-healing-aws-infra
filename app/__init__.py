from flask import Flask

from .db import Database


def create_app(database=None):
    app = Flask(__name__)
    app.extensions["database"] = database or Database()
    return app

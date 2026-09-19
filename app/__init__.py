from flask import Flask

from .db import Database
from .routes import bp


def create_app(database=None):
    app = Flask(__name__)
    app.extensions["database"] = database or Database()
    app.register_blueprint(bp, url_prefix="/api")
    return app

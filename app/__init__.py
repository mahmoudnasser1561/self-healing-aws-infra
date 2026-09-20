from flask import Flask

from .config import load_config
from .db import Database
from .routes import bp


def create_app(config=None, database=None):
    config = config or load_config()
    app = Flask(__name__)
    app.config["CONFIG"] = config
    app.extensions["database"] = database or Database(config)
    app.register_blueprint(bp, url_prefix="/api")
    return app

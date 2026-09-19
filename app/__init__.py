from flask import Flask

from .config import load_settings
from .db import Database
from .errors import register_error_handlers
from .json import JSONProvider
from .routes import bp


def create_app(settings=None, database=None):
    settings = settings or load_settings()
    app = Flask(__name__)
    app.json = JSONProvider(app)
    app.url_map.strict_slashes = False
    app.config["SETTINGS"] = settings
    app.extensions["database"] = database or Database(settings)

    app.register_blueprint(bp, url_prefix="/api")
    register_error_handlers(app)

    return app

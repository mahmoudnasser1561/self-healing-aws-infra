from flask import Blueprint, current_app, jsonify

from . import repository

bp = Blueprint("api", __name__)


def _database():
    return current_app.extensions["database"]


@bp.get("/health")
def health():
    version = current_app.config["SETTINGS"].version
    try:
        with _database().connection() as conn, conn.cursor() as cur:
            status = repository.database_status(cur)
    except Exception:
        current_app.logger.exception("health check failed")
        return jsonify(status="unavailable", version=version), 503
    return jsonify(
        status="ok", version=version, db_time=status["db_time"], todos=status["todos"]
    )

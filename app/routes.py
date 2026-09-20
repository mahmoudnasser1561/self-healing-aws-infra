from flask import Blueprint, current_app, jsonify, request

from . import todos

bp = Blueprint("api", __name__)


def _database():
    return current_app.extensions["database"]


@bp.get("/health")
def health():
    try:
        with _database().cursor() as cur:
            status = todos.status(cur)
    except Exception:
        current_app.logger.exception("health check failed")
        return jsonify(status="unavailable"), 503
    return jsonify(
        status="ok",
        version=current_app.config["CONFIG"].version,
        db_time=status["db_time"].isoformat(),
        todos=status["todos"],
    )


@bp.get("/todos")
def list_all():
    with _database().cursor() as cur:
        return jsonify(todos=todos.list_todos(cur))


@bp.post("/todos")
def create():
    payload = request.get_json(silent=True)
    title = payload.get("title") if isinstance(payload, dict) else None
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 200:
        return jsonify(error="title must be 1 to 200 characters"), 400
    with _database().cursor() as cur:
        return jsonify(todos.add_todo(cur, title.strip())), 201


@bp.delete("/todos/<int:todo_id>")
def remove(todo_id):
    with _database().cursor() as cur:
        todos.delete_todo(cur, todo_id)
    return "", 204

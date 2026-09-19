from flask import Blueprint, abort, current_app, jsonify, request, url_for

from . import repository
from .schemas import (
    ORDERS,
    PRIORITY_MAX,
    PRIORITY_MIN,
    SORT_FIELDS,
    STATUSES,
    TodoCreate,
    TodoUpdate,
    parse_list_params,
)

bp = Blueprint("api", __name__)


def _database():
    return current_app.extensions["database"]


def _settings():
    return current_app.config["SETTINGS"]


def _not_found():
    abort(404, description="todo not found")


@bp.get("/health")
def health():
    version = _settings().version
    try:
        with _database().connection() as conn, conn.cursor() as cur:
            status = repository.database_status(cur)
    except Exception:
        current_app.logger.exception("health check failed")
        return jsonify(status="unavailable", version=version), 503
    return jsonify(
        status="ok", version=version, db_time=status["db_time"], todos=status["todos"]
    )


@bp.get("/todos/options")
def options():
    settings = _settings()
    return jsonify(
        status=list(STATUSES),
        priority=list(range(PRIORITY_MIN, PRIORITY_MAX + 1)),
        sort=list(SORT_FIELDS),
        order=list(ORDERS),
        paging={
            "default_limit": settings.default_limit,
            "max_limit": settings.max_limit,
        },
    )


@bp.get("/todos")
def list_todos():
    params = parse_list_params(request.args, _settings())
    with _database().connection() as conn, conn.cursor() as cur:
        items, total = repository.list_todos(cur, params)
    return jsonify(
        items=items,
        meta={"total": total, "limit": params.limit, "offset": params.offset},
    )


@bp.post("/todos")
def create_todo():
    data = TodoCreate.model_validate(request.get_json())
    with _database().connection() as conn, conn.cursor() as cur:
        todo = repository.create_todo(cur, data.model_dump())
    response = jsonify(todo)
    response.status_code = 201
    response.headers["Location"] = url_for("api.get_todo", todo_id=todo["id"])
    return response


@bp.get("/todos/<int:todo_id>")
def get_todo(todo_id):
    with _database().connection() as conn, conn.cursor() as cur:
        todo = repository.get_todo(cur, todo_id)
    if todo is None:
        _not_found()
    return jsonify(todo)


@bp.patch("/todos/<int:todo_id>")
def update_todo(todo_id):
    changes = TodoUpdate.model_validate(request.get_json()).model_dump(
        exclude_unset=True
    )
    with _database().connection() as conn, conn.cursor() as cur:
        todo = repository.update_todo(cur, todo_id, changes)
    if todo is None:
        _not_found()
    return jsonify(todo)


@bp.delete("/todos/<int:todo_id>")
def delete_todo(todo_id):
    with _database().connection() as conn, conn.cursor() as cur:
        deleted = repository.delete_todo(cur, todo_id)
    if not deleted:
        _not_found()
    return "", 204

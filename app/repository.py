COLUMNS = (
    "id, title, notes, status, priority, due_date, "
    "created_at, updated_at, completed_at"
)
SORT_COLUMNS = {
    "created": "created_at",
    "updated": "updated_at",
    "due": "due_date",
    "priority": "priority",
    "title": "lower(title)",
}
UPDATABLE = ("title", "notes", "status", "priority", "due_date")


def _like_pattern(text):
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _filters(params):
    clauses, values = [], []
    if params.status:
        clauses.append("status = %s")
        values.append(params.status)
    if params.priority is not None:
        clauses.append("priority = %s")
        values.append(params.priority)
    if params.q:
        clauses.append("(title ILIKE %s OR notes ILIKE %s)")
        values.extend([_like_pattern(params.q)] * 2)
    if params.due_from:
        clauses.append("due_date >= %s")
        values.append(params.due_from)
    if params.due_to:
        clauses.append("due_date <= %s")
        values.append(params.due_to)
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    return where, values


def list_todos(cur, params):
    where, values = _filters(params)
    cur.execute(f"SELECT count(*) AS total FROM todos {where}", values)
    total = cur.fetchone()["total"]

    column = SORT_COLUMNS[params.sort]
    direction = params.order.upper()
    cur.execute(
        f"""
        SELECT {COLUMNS} FROM todos {where}
        ORDER BY {column} {direction} NULLS LAST, id {direction}
        LIMIT %s OFFSET %s
        """,
        values + [params.limit, params.offset],
    )
    return cur.fetchall(), total


def get_todo(cur, todo_id):
    cur.execute(f"SELECT {COLUMNS} FROM todos WHERE id = %s", (todo_id,))
    return cur.fetchone()


def create_todo(cur, data):
    cur.execute(
        f"""
        INSERT INTO todos (title, notes, status, priority, due_date, completed_at)
        VALUES (
            %(title)s, %(notes)s, %(status)s, %(priority)s, %(due_date)s,
            CASE WHEN %(status)s = 'done' THEN now() END
        )
        RETURNING {COLUMNS}
        """,
        data,
    )
    return cur.fetchone()


def update_todo(cur, todo_id, changes):
    assignments = [f"{name} = %({name})s" for name in UPDATABLE if name in changes]
    if "status" in changes:
        assignments.append(
            "completed_at = CASE WHEN %(status)s = 'done' "
            "THEN COALESCE(completed_at, now()) END"
        )
    assignments.append("updated_at = now()")
    cur.execute(
        f"""
        UPDATE todos SET {", ".join(assignments)}
        WHERE id = %(id)s
        RETURNING {COLUMNS}
        """,
        {**changes, "id": todo_id},
    )
    return cur.fetchone()


def delete_todo(cur, todo_id):
    cur.execute("DELETE FROM todos WHERE id = %s", (todo_id,))
    return cur.rowcount == 1


def database_status(cur):
    cur.execute("SELECT now() AS db_time, (SELECT count(*) FROM todos) AS todos")
    return cur.fetchone()

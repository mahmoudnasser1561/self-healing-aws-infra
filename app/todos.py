def _todo(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "created_at": row["created_at"].isoformat(),
    }


def list_todos(cur):
    cur.execute("SELECT id, title, created_at FROM todos ORDER BY id DESC")
    return [_todo(row) for row in cur.fetchall()]


def add_todo(cur, title):
    cur.execute(
        "INSERT INTO todos (title) VALUES (%s) RETURNING id, title, created_at",
        (title,),
    )
    return _todo(cur.fetchone())


def delete_todo(cur, todo_id):
    cur.execute("DELETE FROM todos WHERE id = %s", (todo_id,))


def status(cur):
    cur.execute("SELECT now() AS db_time, (SELECT count(*) FROM todos) AS todos")
    return cur.fetchone()

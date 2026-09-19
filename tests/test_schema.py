import psycopg2
import pytest


def insert(cur, **columns):
    names = ", ".join(columns)
    marks = ", ".join(["%s"] * len(columns))
    cur.execute(
        f"INSERT INTO todos ({names}) VALUES ({marks}) RETURNING *",
        list(columns.values()),
    )
    return cur.fetchone()


def test_defaults_describe_a_new_todo(cur):
    row = insert(cur, title="Write docs")

    assert row["status"] == "open"
    assert row["priority"] == 2
    assert row["notes"] == ""
    assert row["due_date"] is None
    assert row["completed_at"] is None
    assert row["created_at"] == row["updated_at"]


@pytest.mark.parametrize(
    "columns",
    [
        {"title": "   "},
        {"title": ""},
        {"title": "x" * 201},
        {"title": "ok", "notes": "n" * 2001},
        {"title": "ok", "status": "blocked"},
        {"title": "ok", "priority": 0},
        {"title": "ok", "priority": 4},
        {"title": "ok", "status": "done"},
        {"title": "ok", "status": "open", "completed_at": "2026-01-01T00:00:00Z"},
    ],
)
def test_the_database_rejects_invalid_rows(cur, columns):
    with pytest.raises(psycopg2.errors.CheckViolation):
        insert(cur, **columns)


def test_a_done_row_needs_a_completion_time(cur):
    row = insert(cur, title="Ship", status="done", completed_at="2026-01-01T00:00:00Z")

    assert row["status"] == "done"
    assert row["completed_at"] is not None

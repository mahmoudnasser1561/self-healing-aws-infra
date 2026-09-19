from datetime import date

from app import repository
from app.schemas import ListParams

TODO = {
    "title": "Task",
    "notes": "",
    "status": "open",
    "priority": 2,
    "due_date": None,
}


def make(cur, **overrides):
    return repository.create_todo(cur, {**TODO, **overrides})


def params(**overrides):
    return ListParams(limit=50, **overrides)


def titles(cur, **overrides):
    items, _ = repository.list_todos(cur, params(**overrides))
    return [item["title"] for item in items]


def test_create_returns_the_stored_row(cur):
    row = make(cur, title="Buy milk", priority=1, due_date=date(2026, 5, 1))

    assert row["id"] > 0
    assert (row["title"], row["priority"], row["due_date"]) == (
        "Buy milk",
        1,
        date(2026, 5, 1),
    )
    assert repository.get_todo(cur, row["id"]) == row


def test_creating_a_done_todo_records_the_completion(cur):
    assert make(cur, status="done")["completed_at"] is not None


def test_get_returns_none_for_a_missing_id(cur):
    assert repository.get_todo(cur, 999999) is None


def test_update_changes_only_the_given_fields(cur):
    row = make(cur, title="Old", notes="keep", priority=3)

    updated = repository.update_todo(cur, row["id"], {"title": "New"})

    assert (updated["title"], updated["notes"], updated["priority"]) == (
        "New",
        "keep",
        3,
    )
    assert updated["updated_at"] >= row["updated_at"]


def test_update_can_clear_the_due_date(cur):
    row = make(cur, due_date=date(2026, 5, 1))

    assert (
        repository.update_todo(cur, row["id"], {"due_date": None})["due_date"] is None
    )


def test_finishing_and_reopening_manage_the_completion_time(cur):
    row = make(cur)

    done = repository.update_todo(cur, row["id"], {"status": "done"})
    assert done["completed_at"] is not None

    again = repository.update_todo(cur, row["id"], {"status": "done"})
    assert again["completed_at"] == done["completed_at"]

    reopened = repository.update_todo(cur, row["id"], {"status": "in_progress"})
    assert reopened["completed_at"] is None


def test_update_of_a_missing_id_returns_none(cur):
    assert repository.update_todo(cur, 999999, {"title": "x"}) is None


def test_delete_reports_whether_a_row_was_removed(cur):
    row = make(cur)

    assert repository.delete_todo(cur, row["id"]) is True
    assert repository.delete_todo(cur, row["id"]) is False


def test_list_defaults_to_newest_first(cur):
    for name in ("a", "b", "c"):
        make(cur, title=name)

    assert titles(cur) == ["c", "b", "a"]


def test_list_filters(cur):
    make(cur, title="Pay rent", status="done", priority=1, due_date=date(2026, 1, 5))
    make(cur, title="Call mom", notes="about the trip", priority=3)
    make(cur, title="Plan trip", status="in_progress", due_date=date(2026, 3, 1))

    assert titles(cur, status="done") == ["Pay rent"]
    assert titles(cur, priority=3) == ["Call mom"]
    assert titles(cur, q="TRIP", sort="title", order="asc") == ["Call mom", "Plan trip"]
    assert titles(cur, due_from=date(2026, 2, 1)) == ["Plan trip"]
    assert titles(cur, due_to=date(2026, 2, 1)) == ["Pay rent"]
    assert titles(cur, status="open", priority=1) == []


def test_search_treats_wildcards_literally(cur):
    make(cur, title="100% done")
    make(cur, title="plain")

    assert titles(cur, q="%") == ["100% done"]
    assert titles(cur, q="_") == []


def test_sorting_puts_missing_due_dates_last(cur):
    make(cur, title="none")
    make(cur, title="late", due_date=date(2026, 9, 1))
    make(cur, title="soon", due_date=date(2026, 1, 1))

    assert titles(cur, sort="due", order="asc") == ["soon", "late", "none"]
    assert titles(cur, sort="due", order="desc") == ["late", "soon", "none"]


def test_paging_reports_the_total(cur):
    for number in range(5):
        make(cur, title=f"t{number}")

    items, total = repository.list_todos(cur, ListParams(limit=2, offset=2))

    assert total == 5
    assert [item["title"] for item in items] == ["t2", "t1"]


def test_database_status_reports_the_clock_and_the_count(cur):
    make(cur)

    status = repository.database_status(cur)

    assert status["todos"] == 1
    assert status["db_time"] is not None

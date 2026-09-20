from datetime import datetime, timezone

from app.todos import _todo


def test_a_row_becomes_json_friendly_fields_only():
    row = {
        "id": 7,
        "title": "Buy milk",
        "created_at": datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
        "internal": "ignored",
    }

    assert _todo(row) == {
        "id": 7,
        "title": "Buy milk",
        "created_at": "2026-01-02T03:04:05+00:00",
    }

from datetime import date, datetime, timezone

import pytest


@pytest.mark.parametrize(
    "payload, field",
    [
        ({}, "title"),
        ({"title": "   "}, "title"),
        ({"title": "ok", "status": "blocked"}, "status"),
        ({"title": "ok", "priority": 4}, "priority"),
        ({"title": "ok", "due_date": "tomorrow"}, "due_date"),
        ({"title": "ok", "surprise": 1}, "surprise"),
    ],
)
def test_create_names_the_invalid_field(client, payload, field):
    response = client.post("/api/todos", json=payload)

    assert response.status_code == 422
    body = response.get_json()
    assert body["error"] == "validation failed"
    assert field in [detail["field"] for detail in body["details"]]


def test_create_rejects_a_body_that_is_not_json(client):
    response = client.post("/api/todos", data="{nope", content_type="application/json")

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_rejects_json_that_is_not_an_object(client):
    assert client.post("/api/todos", json=["a"]).status_code == 422


@pytest.mark.parametrize("payload", [{}, {"title": None}, {"status": "blocked"}])
def test_patch_rejects_invalid_input(client, payload):
    assert client.patch("/api/todos/1", json=payload).status_code == 422


@pytest.mark.parametrize(
    "query",
    [
        "status=blocked",
        "priority=9",
        "sort=id;drop",
        "order=sideways",
        "due_to=soon",
        "limit=0",
        "limit=100000",
        "offset=-1",
    ],
)
def test_list_rejects_invalid_parameters(client, query):
    response = client.get(f"/api/todos?{query}")

    assert response.status_code == 422
    assert response.get_json()["details"]


def test_options_describe_what_the_filter_bar_can_offer(client, settings):
    body = client.get("/api/todos/options").get_json()

    assert body["status"] == ["open", "in_progress", "done"]
    assert body["priority"] == [1, 2, 3]
    assert "created" in body["sort"] and body["order"] == ["asc", "desc"]
    assert body["paging"] == {
        "default_limit": settings.default_limit,
        "max_limit": settings.max_limit,
    }


def test_a_non_numeric_id_is_a_404(client):
    assert client.get("/api/todos/abc").status_code == 404


def test_unknown_routes_and_methods_return_json(client):
    assert "error" in client.get("/api/nothing").get_json()
    assert client.put("/api/todos/1").status_code == 405


def test_dates_and_timestamps_are_serialised_as_iso_8601(client):
    provider = client.application.json

    assert provider.loads(
        provider.dumps(
            {
                "day": date(2026, 5, 1),
                "moment": datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
            }
        )
    ) == {"day": "2026-05-01", "moment": "2026-01-02T03:04:05+00:00"}

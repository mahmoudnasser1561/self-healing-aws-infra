import pytest

TODO = {"title": "Buy milk", "priority": 1, "due_date": "2026-05-01"}


def create(client, **fields):
    response = client.post("/api/todos", json={**TODO, **fields})
    assert response.status_code == 201
    return response.get_json()


def test_create_returns_the_todo_with_its_location(client):
    response = client.post("/api/todos", json=TODO)

    body = response.get_json()
    assert response.status_code == 201
    assert response.headers["Location"] == f"/api/todos/{body['id']}"
    assert body["title"] == "Buy milk"
    assert body["due_date"] == "2026-05-01"
    assert (body["status"], body["notes"], body["completed_at"]) == ("open", "", None)


def test_dates_and_timestamps_are_iso_8601(client):
    body = create(client)

    assert body["created_at"].startswith("20")
    assert "T" in body["created_at"] and "GMT" not in body["created_at"]


def test_create_a_done_todo_stamps_the_completion(client):
    assert create(client, status="done")["completed_at"] is not None


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
def test_create_reports_which_field_is_invalid(client, payload, field):
    response = client.post("/api/todos", json=payload)

    assert response.status_code == 422
    body = response.get_json()
    assert body["error"] == "validation failed"
    assert field in [detail["field"] for detail in body["details"]]


def test_create_rejects_a_body_that_is_not_json(client):
    response = client.post("/api/todos", data="{nope", content_type="application/json")

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_rejects_a_json_body_that_is_not_an_object(client):
    assert client.post("/api/todos", json=["a"]).status_code == 422


def test_get_returns_the_todo_or_404(client):
    todo = create(client)

    assert client.get(f"/api/todos/{todo['id']}").get_json() == todo
    missing = client.get("/api/todos/999999")
    assert missing.status_code == 404
    assert missing.get_json() == {"error": "todo not found"}


def test_a_non_numeric_id_is_a_404(client):
    assert client.get("/api/todos/abc").status_code == 404


def test_patch_updates_only_the_sent_fields(client):
    todo = create(client, notes="keep")

    response = client.patch(f"/api/todos/{todo['id']}", json={"title": "Buy oat milk"})

    body = response.get_json()
    assert response.status_code == 200
    assert (body["title"], body["notes"], body["priority"]) == (
        "Buy oat milk",
        "keep",
        1,
    )
    assert body["updated_at"] >= todo["updated_at"]


def test_patch_manages_the_completion_time(client):
    todo = create(client)
    url = f"/api/todos/{todo['id']}"

    done = client.patch(url, json={"status": "done"}).get_json()
    assert done["completed_at"] is not None

    reopened = client.patch(url, json={"status": "open"}).get_json()
    assert reopened["completed_at"] is None


def test_patch_can_clear_the_due_date(client):
    todo = create(client)

    body = client.patch(f"/api/todos/{todo['id']}", json={"due_date": None}).get_json()

    assert body["due_date"] is None


@pytest.mark.parametrize(
    "payload", [{}, {"title": None}, {"status": "blocked"}, {"surprise": 1}]
)
def test_patch_rejects_invalid_input(client, payload):
    todo = create(client)

    response = client.patch(f"/api/todos/{todo['id']}", json=payload)

    assert response.status_code == 422


def test_patch_of_a_missing_todo_is_a_404(client):
    assert client.patch("/api/todos/999999", json={"title": "x"}).status_code == 404


def test_delete_removes_the_todo(client):
    todo = create(client)

    response = client.delete(f"/api/todos/{todo['id']}")

    assert response.status_code == 204 and response.data == b""
    assert client.get(f"/api/todos/{todo['id']}").status_code == 404
    assert client.delete(f"/api/todos/{todo['id']}").status_code == 404


def test_list_is_paged_and_newest_first(client):
    for number in range(5):
        create(client, title=f"t{number}")

    response = client.get("/api/todos?limit=2&offset=1")

    body = response.get_json()
    assert [item["title"] for item in body["items"]] == ["t3", "t2"]
    assert body["meta"] == {"total": 5, "limit": 2, "offset": 1}


def test_list_uses_the_configured_default_limit(client, settings):
    body = client.get("/api/todos").get_json()

    assert body["meta"]["limit"] == settings.default_limit


def test_list_filters_and_sorts_from_the_query_string(client):
    create(client, title="Pay rent", status="done", priority=3, due_date="2026-01-05")
    create(client, title="Call mom", notes="trip plans", priority=1, due_date=None)
    create(client, title="Plan trip", priority=2, due_date="2026-03-01")

    def titles(query):
        items = client.get(f"/api/todos?{query}").get_json()["items"]
        return [item["title"] for item in items]

    assert titles("status=done") == ["Pay rent"]
    assert titles("priority=1") == ["Call mom"]
    assert titles("q=trip&sort=title&order=asc") == ["Call mom", "Plan trip"]
    assert titles("due_from=2026-02-01") == ["Plan trip"]
    assert titles("sort=due&order=asc") == ["Pay rent", "Plan trip", "Call mom"]
    assert titles("status=&q=&priority=") == ["Plan trip", "Call mom", "Pay rent"]


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


def test_every_option_is_accepted_by_the_list_endpoint(client):
    options = client.get("/api/todos/options").get_json()

    for status in options["status"]:
        assert client.get(f"/api/todos?status={status}").status_code == 200
    for priority in options["priority"]:
        assert client.get(f"/api/todos?priority={priority}").status_code == 200
    for field in options["sort"]:
        assert client.get(f"/api/todos?sort={field}").status_code == 200


def test_unknown_routes_return_json(client):
    response = client.get("/api/nothing")

    assert response.status_code == 404
    assert "error" in response.get_json()

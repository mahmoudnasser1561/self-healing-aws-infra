import pytest

from app import create_app


def test_the_app_exposes_exactly_the_intended_routes(client):
    routes = {
        (rule.rule, method)
        for rule in client.application.url_map.iter_rules()
        for method in rule.methods - {"HEAD", "OPTIONS"}
        if rule.rule.startswith("/api")
    }

    assert routes == {
        ("/api/health", "GET"),
        ("/api/todos", "GET"),
        ("/api/todos", "POST"),
        ("/api/todos/<int:todo_id>", "DELETE"),
    }


def test_creating_the_app_does_not_connect_to_the_database(config):
    assert create_app(config) is not None


@pytest.mark.parametrize(
    "body",
    [
        None,
        "not json",
        ["title"],
        {},
        {"title": None},
        {"title": 5},
        {"title": ""},
        {"title": "   "},
        {"title": "x" * 201},
    ],
)
def test_create_rejects_a_missing_or_invalid_title(client, body):
    response = client.post("/api/todos", json=body)

    assert response.status_code == 400
    assert response.get_json() == {"error": "title must be 1 to 200 characters"}


def test_delete_needs_a_numeric_id(client):
    assert client.delete("/api/todos/abc").status_code == 404


def test_health_reports_unavailable_when_the_database_cannot_be_reached(client):
    response = client.get("/api/health")

    assert response.status_code == 503
    assert response.get_json() == {"status": "unavailable"}

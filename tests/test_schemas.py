from datetime import date

import pytest
from pydantic import ValidationError

from app.errors import RequestError
from app.schemas import (
    ListParams,
    TodoCreate,
    TodoUpdate,
    parse_list_params,
)


def test_create_applies_defaults_and_trims_the_title():
    todo = TodoCreate(title="  Buy milk  ")

    assert todo.model_dump() == {
        "title": "Buy milk",
        "notes": "",
        "status": "open",
        "priority": 2,
        "due_date": None,
    }


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": "   "},
        {"title": "x" * 201},
        {"title": "ok", "notes": "n" * 2001},
        {"title": "ok", "status": "blocked"},
        {"title": "ok", "priority": 4},
        {"title": "ok", "priority": "high"},
        {"title": "ok", "due_date": "tomorrow"},
        {"title": "ok", "surprise": 1},
    ],
)
def test_create_rejects_invalid_input(payload):
    with pytest.raises(ValidationError):
        TodoCreate.model_validate(payload)


def test_update_keeps_only_the_fields_that_were_sent():
    update = TodoUpdate.model_validate({"title": "New", "due_date": None})

    assert update.model_dump(exclude_unset=True) == {"title": "New", "due_date": None}


@pytest.mark.parametrize(
    "payload",
    [{}, {"title": None}, {"status": None}, {"priority": 9}, {"surprise": 1}],
)
def test_update_rejects_invalid_input(payload):
    with pytest.raises(ValidationError):
        TodoUpdate.model_validate(payload)


def test_list_params_use_the_configured_default_limit(settings):
    params = parse_list_params({}, settings)

    assert params.limit == settings.default_limit
    assert (params.sort, params.order, params.offset) == ("created", "desc", 0)


def test_list_params_ignore_blank_values(settings):
    params = parse_list_params({"status": "", "q": "", "limit": ""}, settings)

    assert params.status is None and params.q is None


def test_list_params_are_parsed_from_strings(settings):
    params = parse_list_params(
        {"priority": "1", "due_from": "2026-02-01", "limit": "5", "offset": "10"},
        settings,
    )

    assert (params.priority, params.due_from) == (1, date(2026, 2, 1))
    assert (params.limit, params.offset) == (5, 10)


@pytest.mark.parametrize(
    "args",
    [
        {"status": "blocked"},
        {"priority": "0"},
        {"sort": "id; DROP TABLE todos"},
        {"order": "sideways"},
        {"due_from": "soon"},
        {"offset": "-1"},
        {"limit": "0"},
        {"limit": "abc"},
    ],
)
def test_list_params_reject_invalid_values(settings, args):
    with pytest.raises(RequestError):
        parse_list_params(args, settings)


def test_the_limit_ceiling_comes_from_settings(settings):
    with pytest.raises(RequestError) as error:
        parse_list_params({"limit": str(settings.max_limit + 1)}, settings)

    assert str(settings.max_limit) in error.value.details[0]["message"]


def test_list_params_model_has_no_hardcoded_limit():
    assert ListParams().limit is None

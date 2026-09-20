from app import repository
from app.schemas import SORT_FIELDS, ListParams, TodoUpdate


def test_every_sort_field_maps_to_a_column():
    assert set(repository.SORT_COLUMNS) == set(SORT_FIELDS)


def test_updatable_columns_match_the_update_model():
    assert set(repository.UPDATABLE) == set(TodoUpdate.model_fields)


def test_search_treats_wildcards_literally():
    assert repository._like_pattern("100%_x\\") == "%100\\%\\_x\\\\%"


def test_no_filters_means_no_where_clause():
    assert repository._filters(ListParams()) == ("", [])


def test_filters_combine_with_and_and_keep_values_in_order():
    params = ListParams(status="done", priority=1, q="milk")

    where, values = repository._filters(params)

    assert where == (
        "WHERE status = %s AND priority = %s AND (title ILIKE %s OR notes ILIKE %s)"
    )
    assert values == ["done", 1, "%milk%", "%milk%"]
